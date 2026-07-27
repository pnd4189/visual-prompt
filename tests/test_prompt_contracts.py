#!/usr/bin/env python3
"""Regression tests for prompt parsing, music plans, batch resume, and history."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import check_prompt_similarity as similarity  # type: ignore  # noqa: E402
import check_anchor_consistency as anchors  # type: ignore  # noqa: E402
import assemble_outputs  # type: ignore  # noqa: E402
import calc_scene_count  # type: ignore  # noqa: E402
import validate_artifacts as artifacts  # type: ignore  # noqa: E402
import validate_scene_plan as scene_plan_validator  # type: ignore  # noqa: E402


def music_paragraph(name: str) -> str:
    prefix = (
        f'Gentle {name} opens beneath narration with warm guzheng harmonics, '
        'breathy dizi, quiet strings, and a restrained frame drum. The melody '
        'moves through a spacious minor pentatonic atmosphere at 68 BPM, holding '
        'soft emotional tension while natural room reverb leaves every spoken '
        'word clear and centered.'
    ).split()
    ending = artifacts._MUSIC_ENDING.split()
    while len(prefix) + len(ending) < 55:
        prefix.append('softly')
    return ' '.join(prefix + ending)


def music_body(name: str) -> str:
    tags = (
        'guzheng, dizi, erhu, ambient, restrained, emotional, pentatonic, '
        'soft percussion, underscore, spacious, narration, instrumental'
    )
    return f'{music_paragraph(name)}\n\nTags: {tags}'


class IdentityAnchorTests(unittest.TestCase):
    def test_existing_numeric_bible_anchor_stays_compatible(self):
        bible = (
            '| name | age | build | hair | face | signature mark | attire base | role |\n'
            '|---|---|---|---|---|---|---|---|\n'
            '| Lan | 22 | tall, lean | black hair | narrow eyes | jade pendant | '
            'grey robe | protagonist |\n'
        )

        parsed = anchors.parse_bible(bible)

        self.assertEqual(
            'Lan — 22 years old, tall, lean build, black hair, narrow eyes, '
            'jade pendant, grey robe.',
            parsed['Lan']['anchor'],
        )

    def test_unknown_bible_fields_stay_explicit_in_anchor(self):
        bible = (
            '| name | age | build | hair | face | signature mark | attire base | role |\n'
            '|---|---|---|---|---|---|---|---|\n'
            '| Tiểu Phàm | not stated | not stated | black hair | not stated | '
            'not stated | grey robe | protagonist |\n'
        )

        parsed = anchors.parse_bible(bible)

        self.assertEqual(
            'Tiểu Phàm — age not stated, build not stated, black hair, '
            'face not stated, signature mark not stated, grey robe.',
            parsed['Tiểu Phàm']['anchor'],
        )

    def test_anchor_fix_replaces_invented_visual_fields(self):
        bible = (
            '| name | age | build | hair | face | signature mark | attire base | role |\n'
            '|---|---|---|---|---|---|---|---|\n'
            '| Tiểu Phàm | not stated | not stated | not stated | not stated | '
            'not stated | not stated | protagonist |\n'
        )
        parsed = anchors.parse_bible(bible)
        invented = (
            'Subject: Tiểu Phàm — 22 years old, tall build, long black hair, '
            'sharp eyes, jade pendant, grey robe.'
        )

        fixed, count = anchors.fix_text(invented, parsed)

        self.assertEqual(1, count)
        self.assertIn('age not stated, build not stated', fixed)
        self.assertNotIn('jade pendant', fixed)


class PromptSimilarityTests(unittest.TestCase):
    def test_canonical_music_blocks_are_parsed_and_compared(self):
        body = music_body('mountain mist')
        loops = similarity.parse_music(f'{body}\n\n{body}\n')

        self.assertEqual([1, 2], [loop['scene_id'] for loop in loops])
        result = similarity.check_music(loops)
        self.assertTrue(any(item['type'] == 'music_body_copy' for item in result['violations']))
        self.assertTrue(any(item['type'] == 'music_intro_copy' for item in result['violations']))

    def test_assembled_music_round_trip_populates_gate_and_history(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            work = directory / '.work'
            work.mkdir()
            input_path = directory / 'novel.txt'
            input_path.write_text('Chương 1. Test\n', encoding='utf-8')
            (work / 'scene-001.md').write_text(
                '---\nscene_id: 1\ncache_key: abc\nsource_anchor: test source\n'
                'has_video: false\n---\n'
                '## Image Prompt\nCamera: wide frame\n',
                encoding='utf-8',
            )
            body = music_body('river dusk')
            for index in (1, 2):
                (work / f'music-{index:03d}.md').write_text(
                    f'---\nloop_index: {index}\n---\n{body}\n', encoding='utf-8',
                )

            assembled = assemble_outputs.assemble(
                input_path, work, no_video=True, no_music=False,
            )
            music_text = Path(assembled['music_path']).read_text(encoding='utf-8')
            loops = similarity.parse_music(music_text)
            result = similarity.check_music(loops)
            history = similarity._history_values(
                Path(assembled['image_path']).read_text(encoding='utf-8'), music_text,
            )

        self.assertEqual(2, len(loops))
        self.assertTrue(result['violations'])
        self.assertEqual(2, len(history['music intros used']))
        self.assertTrue(history['music tags used'])

    def test_alphanumeric_scene_id_is_preserved(self):
        text = (
            '--- SCENE 026 ---\nCamera: wide frame\n\n'
            '--- SCENE 026b ---\nCamera: close frame\n'
        )

        scenes = similarity.parse_image(text)

        self.assertEqual([26, '026b'], [scene['scene_id'] for scene in scenes])
        rewrite = similarity._rewrite_scene_ids([
            {'scene_a': 26, 'scene_b': '026b'},
        ])
        self.assertEqual(['026b'], rewrite)

    def test_nonempty_unparseable_input_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            bad_prompt = Path(temp_dir) / 'bad-prompt.txt'
            bad_prompt.write_text('nonempty text without a block marker\n', encoding='utf-8')
            for kind in ('image', 'music', 'video'):
                with self.subTest(kind=kind):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPTS / 'check_prompt_similarity.py'),
                         f'--{kind}', str(bad_prompt)],
                        cwd=ROOT, capture_output=True, text=True, check=False,
                    )
                    payload = json.loads(result.stdout)
                    self.assertEqual(1, result.returncode)
                    self.assertFalse(payload['ok'])
                    self.assertIn('no parseable blocks', payload['error'])

    def test_malformed_canonical_music_block_does_not_merge_into_next_block(self):
        malformed = f'orphan paragraph without tags\n\n{music_body("valid region")}\n'

        self.assertEqual([], similarity.parse_music(malformed))

    def test_duplicate_ids_and_empty_image_fields_fail_validation(self):
        duplicate = similarity.parse_image(
            '--- SCENE 001 ---\nCamera: wide\n'
            '--- SCENE 001 ---\nCamera: close\n'
        )
        empty_fields = similarity.parse_image(
            '--- SCENE 002 ---\nUnknown Label: no canonical fields\n'
        )

        with self.assertRaisesRegex(ValueError, 'duplicate block ids'):
            similarity._require_blocks('image', 'nonempty', duplicate)
        with self.assertRaisesRegex(ValueError, 'no comparable fields'):
            similarity._require_image_fields(empty_fields)

    def test_concurrent_history_updates_do_not_lose_entries(self):
        processes = []
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_path = Path(temp_dir)
            history = temp_path / 'series-history.md'
            history.with_name(f'.{history.name}.lock').write_text(
                '99999999', encoding='ascii',
            )
            for index in range(8):
                image = temp_path / f'image-{index}.txt'
                image.write_text(
                    f'--- SCENE 001 ---\nCamera: unique angle {index}\n'
                    f'Setting: unique setting {index}.\n'
                    f'Action / Energy: unique action {index}\n',
                    encoding='utf-8',
                )
                processes.append(subprocess.Popen(
                    [sys.executable, str(SCRIPTS / 'check_prompt_similarity.py'),
                     '--extract-history', '--image', str(image), '--history', str(history)],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                ))
            results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
            history_text = history.read_text(encoding='utf-8')

        self.assertTrue(all(returncode == 0 for _, _, returncode in results), results)
        for index in range(8):
            self.assertIn(f'unique angle {index}', history_text)


class MusicPlanTests(unittest.TestCase):
    def _write_valid_fixture(self, directory: Path):
        context = ('a' * 12, 'tien-hiep', 'b' * 12, 'c' * 12)
        regions = [
            {'loop_index': 1, 'chapter_start': 121, 'chapter_end': 125, 'mood': 'calm/intro'},
            {'loop_index': 2, 'chapter_start': 126, 'chapter_end': 130, 'mood': 'tension/battle'},
        ]
        plan_key = artifacts._cache_key(*context[:3], '2')
        plan = directory / 'music-plan.md'
        (directory / 'chapters_qa.json').write_text(
            json.dumps([{'id': chapter_id} for chapter_id in range(121, 131)]),
            encoding='utf-8',
        )
        for value, filename in zip(
            (context[0], context[1], context[2], context[3]),
            ('qa.hash', 'genre.txt', 'plan.hash', 'style.hash'),
        ):
            (directory / filename).write_text(f'{value}\n', encoding='utf-8')
        plan.write_text(
            f'---\ncache_key: {plan_key}\nqa_hash: {context[0]}\n'
            f'genre: {context[1]}\nplan_hash: {context[2]}\n'
            f'style_hash: {context[3]}\nmusic_n: 2\n---\n'
            '| loop_index | chapter_start | chapter_end | mood |\n'
            '|---:|---:|---:|---|\n'
            '| 1 | 121 | 125 | calm/intro |\n'
            '| 2 | 126 | 130 | tension/battle |\n',
            encoding='utf-8',
        )
        for region in regions:
            index = region['loop_index']
            cache_key = artifacts._cache_key(
                *context, artifacts._region_payload(region, len(regions)),
            )
            (directory / f'music-{index:03d}.md').write_text(
                '---\n'
                f'loop_index: {index}\n'
                'total: 2\n'
                f'chapter_start: {region["chapter_start"]}\n'
                f'chapter_end: {region["chapter_end"]}\n'
                f'mood: {region["mood"]}\n'
                f'cache_key: {cache_key}\n'
                '---\n'
                f'{music_body(f"region {index}")}\n',
                encoding='utf-8',
            )
        return context, plan

    def test_valid_music_plan_and_loop_metadata_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            context, plan = self._write_valid_fixture(directory)

            result = artifacts.check_music(directory, 2, plan, context)
            external_result = artifacts.check_music(directory, 2, plan)

        self.assertTrue(result['ok'], result['errors'])
        self.assertTrue(external_result['ok'], external_result['errors'])

    def test_malformed_plan_and_stale_metadata_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            context, plan = self._write_valid_fixture(directory)
            plan.write_text(
                '---\ncache_key: 0000000000000000\n---\n'
                '| loop_index | chapter_start | chapter_end | mood |\n'
                '|---:|---:|---:|---|\n'
                '| 1 | 130 | 121 | unknown |\n',
                encoding='utf-8',
            )
            first_loop = directory / 'music-001.md'
            first_loop.write_text(
                first_loop.read_text(encoding='utf-8').replace(
                    'loop_index: 1', 'loop_index: 999', 1,
                ),
                encoding='utf-8',
            )

            result = artifacts.check_music(directory, 2, plan, context)

        self.assertFalse(result['ok'])
        joined = '\n'.join(result['errors'])
        self.assertIn('chapter range is reversed', joined)
        self.assertIn('unsupported mood', joined)
        self.assertIn('has 1 regions, expected 2', joined)
        self.assertIn('cache_key is stale', joined)
        self.assertIn('loop_index does not match filename', joined)
        self.assertIn('chapter coverage does not match', joined)

    def test_explicit_missing_music_plan_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            missing = directory / 'missing-plan.md'

            result = artifacts.check_music(directory, 0, missing)

        self.assertFalse(result['ok'])
        self.assertIn('missing explicit music plan', '\n'.join(result['errors']))

    def test_music_plan_rejects_extra_schema_column_and_negative_chapters(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            plan = Path(temp_dir) / 'music-plan.md'
            plan.write_text(
                '| loop_index | chapter_start | chapter_end | mood | extra |\n'
                '|---:|---:|---:|---|---|\n'
                '| 1 | -3 | -1 | calm/intro | value |\n',
                encoding='utf-8',
            )
            _, extra_column_errors = artifacts.parse_music_plan(plan)
            plan.write_text(
                '| loop_index | chapter_start | chapter_end | mood |\n'
                '|---:|---:|---:|---|\n'
                '| 1 | -3 | -1 | calm/intro |\n',
                encoding='utf-8',
            )
            _, negative_range_errors = artifacts.parse_music_plan(plan)

        self.assertIn('missing music plan schema header', '\n'.join(extra_column_errors))
        self.assertIn('chapter ids must be positive', '\n'.join(negative_range_errors))

    def test_external_validation_detects_hash_file_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            _, plan = self._write_valid_fixture(directory)
            (directory / 'qa.hash').write_text(f'{"d" * 12}\n', encoding='utf-8')

            result = artifacts.check_music(directory, 2, plan)

        self.assertFalse(result['ok'])
        self.assertIn('qa_hash is stale', '\n'.join(result['errors']))

    def test_external_validation_detects_genre_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            _, plan = self._write_valid_fixture(directory)
            (directory / 'genre.txt').write_text('vo-hiep\n', encoding='utf-8')

            result = artifacts.check_music(directory, 2, plan)

        self.assertFalse(result['ok'])
        self.assertIn('genre is stale', '\n'.join(result['errors']))

    def test_music_plan_requires_chapter_source_and_rejects_unneeded_overlap(self):
        regions = [
            {'loop_index': 1, 'chapter_start': 1, 'chapter_end': 2, 'mood': 'calm/intro'},
            {'loop_index': 2, 'chapter_start': 2, 'chapter_end': 3, 'mood': 'sad/reflection'},
        ]
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            missing_errors = artifacts._chapter_coverage_errors(directory, regions)
            (directory / 'chapters_qa.json').write_text(
                '[{"id": 1}, {"id": 2}, {"id": 3}]', encoding='utf-8',
            )
            overlap_errors = artifacts._chapter_coverage_errors(directory, regions)
            huge_range_errors = artifacts._chapter_coverage_errors(directory, [{
                'loop_index': 1, 'chapter_start': 1,
                'chapter_end': 10**12, 'mood': 'calm/intro',
            }])

        self.assertIn('missing chapter source', '\n'.join(missing_errors))
        self.assertIn('overlap unnecessarily', '\n'.join(overlap_errors))
        self.assertIn('falls outside', '\n'.join(huge_range_errors))

    def test_same_chapter_regions_are_allowed_when_music_count_is_larger(self):
        regions = [
            {'loop_index': 1, 'chapter_start': 1, 'chapter_end': 1, 'mood': 'calm/intro'},
            {'loop_index': 2, 'chapter_start': 1, 'chapter_end': 1, 'mood': 'sad/reflection'},
        ]
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            (directory / 'chapters_qa.json').write_text('[{"id": 1}]', encoding='utf-8')

            errors = artifacts._chapter_coverage_errors(directory, regions)

        self.assertEqual([], errors)

    def test_forbidden_music_tag_is_rejected(self):
        body = music_body('quiet valley').replace('narration, instrumental', 'narration, battle')

        errors = artifacts._music_body_errors(body)

        self.assertIn('forbidden tag', '\n'.join(errors))

    def test_duplicate_music_tags_are_rejected(self):
        body = f'{music_paragraph("quiet valley")}\n\nTags: ' + ', '.join(['guzheng'] * 12)

        errors = artifacts._music_body_errors(body)

        self.assertIn('duplicate tags', '\n'.join(errors))

    def test_four_digit_music_filename_is_supported(self):
        self.assertEqual(1000, artifacts._music_index('music-1000.md'))
        self.assertIsNotNone(artifacts._MUSIC_FILE_RE.fullmatch('music-1000.md'))


class ArtifactSceneIdTests(unittest.TestCase):
    def test_alphanumeric_scene_plan_matches_scene_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            plan = directory / 'scene-plan.md'
            plan.write_text(
                'Genre: tien-hiep · Images: 1 · Videos: 0 · Chapters: 1\n\n'
                '| scene_id | chapter | source_anchor | scene_tag | characters | synopsis | setting_plan | camera_plan | action_plan | palette_plan | video? |\n'
                '|---|---|---|---|---|---|---|---|---|---|---|\n'
                '| 026b | 121 | Lan raises the jade seal slowly in silence | detail | Lan | Lan raises the jade seal slowly. | stone chamber | close 50mm | raises seal | warm jade | |\n',
                encoding='utf-8',
            )
            (directory / 'scene-026b.md').write_text(
                '---\nscene_id: 026b\ncache_key: 0000000000000000\n'
                'source_anchor: Lan raises the jade seal slowly in silence\n'
                'has_video: false\n---\n'
                '## Image Prompt\nCamera: close frame\n',
                encoding='utf-8',
            )

            result = artifacts.check_scenes(directory, plan)
            scene_path = directory / 'scene-026b.md'
            scene_path.write_text(
                scene_path.read_text(encoding='utf-8').replace(
                    'source_anchor: Lan raises the jade seal slowly in silence',
                    'source_anchor: invented anchor',
                    1,
                ),
                encoding='utf-8',
            )
            anchor_mismatch = artifacts.check_scenes(directory, plan)
            scene_path.write_text(
                scene_path.read_text(encoding='utf-8').replace(
                    'source_anchor: invented anchor',
                    'source_anchor: Lan raises the jade seal slowly in silence',
                    1,
                ),
                encoding='utf-8',
            )
            scene_path.write_text(
                scene_path.read_text(encoding='utf-8').replace(
                    'scene_id: 026b', 'scene_id: 999', 1,
                ),
                encoding='utf-8',
            )
            mismatched_result = artifacts.check_scenes(directory, plan)

        self.assertTrue(result['ok'], result['errors'])
        self.assertFalse(anchor_mismatch['ok'])
        self.assertIn('source_anchor does not match', '\n'.join(anchor_mismatch['errors']))
        self.assertFalse(mismatched_result['ok'])
        self.assertIn('scene_id does not match', '\n'.join(mismatched_result['errors']))

    def test_case_insensitive_scene_id_collision_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            plan = directory / 'scene-plan.md'
            plan.write_text(
                'Genre: tien-hiep · Images: 2 · Videos: 0 · Chapters: 1\n\n'
                '| scene_id | chapter | source_anchor | scene_tag | characters | synopsis | setting_plan | camera_plan | action_plan | palette_plan | video? |\n'
                '|---|---|---|---|---|---|---|---|---|---|---|\n'
                '| 026A | 121 | Lan raises the bronze seal slowly in silence | detail | Lan | Lan raises the bronze seal slowly. | stone chamber | close 50mm | raises seal | warm bronze | |\n'
                '| 026a | 121 | Lan raises the jade seal slowly in silence | detail | Lan | Lan raises the jade seal slowly. | stone chamber | close 85mm | raises seal | cool jade | |\n',
                encoding='utf-8',
            )
            (directory / 'scene-026a.md').write_text(
                '---\nscene_id: 026a\ncache_key: 0000000000000000\n'
                'source_anchor: Lan raises the bronze seal slowly in silence\n'
                'has_video: false\n---\n'
                '## Image Prompt\nCamera: close frame\n',
                encoding='utf-8',
            )

            result = artifacts.check_scenes(directory, plan)

        self.assertFalse(result['ok'])
        self.assertIn('duplicate scene ids', '\n'.join(result['errors']))

    def test_output_count_uses_anchored_scene_markers(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output = Path(temp_dir) / 'image.txt'
            output.write_text(
                '--- SCENE 001 ---\nCamera: wide\n'
                'Body mentions fake --- SCENE marker without a separator.\n',
                encoding='utf-8',
            )
            errors = []

            artifacts._check_output_file(output, 2, errors)

        self.assertIn('has 1 blocks, expected 2', '\n'.join(errors))

    def test_output_scene_ids_and_order_must_match_plan(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output = Path(temp_dir) / 'image.txt'
            output.write_text(
                '--- SCENE 003 ---\nCamera: wide\n'
                '--- SCENE 004 ---\nCamera: close\n',
                encoding='utf-8',
            )
            errors = []

            artifacts._check_output_file(output, 2, errors, ['001', '002'])

        self.assertIn('scene ids/order do not match', '\n'.join(errors))

    def test_malformed_scene_row_cannot_reduce_declared_count(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            plan = directory / 'scene-plan.md'
            plan.write_text(
                'Genre: tien-hiep · Images: 2 · Videos: 0 · Chapters: 1\n\n'
                '| scene_id | chapter | source_anchor | scene_tag | characters | synopsis | setting_plan | camera_plan | action_plan | palette_plan | video? |\n'
                '|---|---|---|---|---|---|---|---|---|---|---|\n'
                '| 001 | 1 | Lan raises the bronze seal slowly in silence | detail | Lan | Lan raises the bronze seal slowly. | stone chamber | close 50mm | raises seal | warm bronze | |\n'
                '| BAD | 1 | Lan raises the jade seal slowly in silence | detail | Lan | Lan raises the jade seal slowly. | stone chamber | close 85mm | raises seal | cool jade | |\n',
                encoding='utf-8',
            )
            (directory / 'scene-001.md').write_text(
                '---\nscene_id: 001\ncache_key: 0000000000000000\n'
                'source_anchor: Lan raises the bronze seal slowly in silence\n'
                'has_video: false\n---\n'
                '## Image Prompt\nCamera: close frame\n',
                encoding='utf-8',
            )
            input_path = directory / 'novel.txt'
            input_path.write_text('Chương 1. Test\n', encoding='utf-8')
            (directory / 'novel_image_prompts.txt').write_text(
                '--- SCENE 001 ---\nCamera: close frame\n', encoding='utf-8',
            )

            plan_result = scene_plan_validator.validate(plan.read_text(encoding='utf-8'))
            artifact_result = artifacts.check_scenes(directory, plan)
            output_result = artifacts.check_outputs(input_path, 1, 0, 0, plan)

        self.assertFalse(plan_result['ok'])
        self.assertIn('invalid scene_id BAD', str(plan_result['violations']))
        self.assertFalse(artifact_result['ok'])
        self.assertEqual(2, artifact_result['expected'])
        self.assertIn('parsed scene count 1', '\n'.join(artifact_result['errors']))
        self.assertFalse(output_result['ok'])
        self.assertIn('invalid scene_id BAD', '\n'.join(output_result['errors']))


class GroundingAndMediaDefaultTests(unittest.TestCase):
    @staticmethod
    def _grounded_plan(
        anchor: str = 'Lan bước vào sân đá khi gió lay cành tùng',
        character: str = 'Lan',
        second_camera: str = 'low oblique 35mm',
    ) -> str:
        return (
            'Genre: tien-hiep · Images: 2 · Videos: 0 · Chapters: 1\n\n'
            '| scene_id | chapter | source_anchor | scene_tag | characters | synopsis | setting_plan | camera_plan | action_plan | palette_plan | video? |\n'
            '|---|---|---|---|---|---|---|---|---|---|---|\n'
            f'| 001 | 1 | {anchor} | establishing | {character} | Lan enters the stone courtyard. | stone courtyard and pine wall | high wide 24mm | Lan crosses the threshold | cool daylight and pine green | |\n'
            f'| 002 | 1 | Nàng nâng ngọc ấn lên trước cánh cửa khép kín | reveal | Lan | Lan raises the jade seal before the door. | closed timber door and stone step | {second_camera} | Lan raises the seal | warm jade against grey stone | |\n'
        )

    def test_grounded_plan_accepts_exact_source_anchors(self):
        chapters = [{
            'id': 1,
            'text': (
                'Lan bước vào sân đá khi gió lay cành tùng. '
                'Nàng nâng ngọc ấn lên trước cánh cửa khép kín.'
            ),
        }]

        result = scene_plan_validator.validate(self._grounded_plan(), chapters)

        self.assertTrue(result['ok'], result['violations'])

    def test_grounding_rejects_invented_anchor_and_character(self):
        chapters = [{
            'id': 1,
            'text': (
                'Lan bước vào sân đá khi gió lay cành tùng. '
                'Nàng nâng ngọc ấn lên trước cánh cửa khép kín.'
            ),
        }]

        result = scene_plan_validator.validate(
            self._grounded_plan(
                anchor='Minh triệu hồi một đạo quân giữa cơn bão lớn',
                character='Minh',
            ),
            chapters,
        )
        kinds = {item['type'] for item in result['violations']}

        self.assertIn('ungrounded_source_anchor', kinds)
        self.assertIn('ungrounded_character', kinds)

    def test_adjacent_visual_reuse_fails(self):
        chapters = [{
            'id': 1,
            'text': (
                'Lan bước vào sân đá khi gió lay cành tùng. '
                'Nàng nâng ngọc ấn lên trước cánh cửa khép kín.'
            ),
        }]

        result = scene_plan_validator.validate(
            self._grounded_plan(second_camera='high wide 24mm'),
            chapters,
        )

        self.assertIn(
            'adjacent_visual_repeat',
            {item['type'] for item in result['violations']},
        )

    def test_source_anchors_cannot_reverse_story_order(self):
        chapters = [{
            'id': 1,
            'text': (
                'Lan bước vào sân đá khi gió lay cành tùng. '
                'Nàng nâng ngọc ấn lên trước cánh cửa khép kín.'
            ),
        }]
        first = 'Lan bước vào sân đá khi gió lay cành tùng'
        second = 'Nàng nâng ngọc ấn lên trước cánh cửa khép kín'
        reversed_plan = (
            self._grounded_plan()
            .replace(first, '__FIRST_ANCHOR__', 1)
            .replace(second, first, 1)
            .replace('__FIRST_ANCHOR__', second, 1)
        )

        result = scene_plan_validator.validate(reversed_plan, chapters)

        self.assertIn(
            'story_order',
            {item['type'] for item in result['violations']},
        )

    def test_image_only_is_the_default_count_and_assembly_mode(self):
        counts = calc_scene_count.compute(12_000, None, None)
        video_counts = calc_scene_count.compute(
            12_000, None, None, video_enabled=True,
        )
        self.assertEqual(0, counts['videos'])
        self.assertGreaterEqual(video_counts['videos'], 20)

        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            work = directory / '.work'
            work.mkdir()
            input_path = directory / 'novel.txt'
            input_path.write_text('Chương 1. Test\n', encoding='utf-8')
            (work / 'scene-001.md').write_text(
                '---\nscene_id: 001\ncache_key: 0000000000000000\n'
                'source_anchor: Chương một có một cảnh thử nghiệm ngắn\n'
                'has_video: true\n---\n## Image Prompt\nCamera: wide\n'
                '## Video Prompt\nCinematography: slow push\n',
                encoding='utf-8',
            )
            (work / 'music-001.md').write_text(
                '---\nloop_index: 1\n---\nMusic body\n', encoding='utf-8',
            )

            summary = assemble_outputs.assemble(input_path, work)

            self.assertIsNone(summary['video_path'])
            self.assertIsNone(summary['music_path'])
            self.assertFalse((directory / 'novel_video_prompts.txt').exists())
            self.assertFalse((directory / 'novel_music_prompts.txt').exists())

    def test_video_count_never_exceeds_effective_image_count(self):
        counts = calc_scene_count.compute(
            1_000, 3, None, video_enabled=True,
        )
        self.assertEqual(3, counts['videos'])
        with self.assertRaisesRegex(ValueError, 'cannot exceed'):
            calc_scene_count.compute(1_000, 3, 4)

    def test_nested_runtime_code_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            work = directory / '.work'
            nested = work / 'hidden'
            nested.mkdir(parents=True)
            (nested / 'generate-scenes.sh').write_text(
                '#!/usr/bin/env bash\necho generated\n', encoding='utf-8',
            )
            image = directory / 'image.txt'
            image.write_text(
                '--- SCENE 001 ---\n'
                'Camera: wide\nStory DNA: grounded\nSetting: courtyard\n'
                'Composition: foreground and background\nSubject: Lan\n'
                'Action / Energy: walking\nStyle: painted\n'
                'Lighting / Color: daylight\nAtmosphere: quiet\nNegative: logo\n',
                encoding='utf-8',
            )

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / 'check_run_legit.py'),
                    '--work', str(work), '--image', str(image),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )

        self.assertEqual(2, result.returncode)
        self.assertIn('runtime code', result.stdout)

    def test_plain_python_runtime_code_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            work = directory / '.work'
            work.mkdir()
            (work / 'helper.py').write_text(
                'items = list(range(3))\n', encoding='utf-8',
            )
            image = directory / 'image.txt'
            image.write_text(
                '--- SCENE 001 ---\n'
                'Camera: wide\nStory DNA: grounded\nSetting: courtyard\n'
                'Composition: foreground and background\nSubject: Lan\n'
                'Action / Energy: walking\nStyle: painted\n'
                'Lighting / Color: daylight\nAtmosphere: quiet\nNegative: logo\n',
                encoding='utf-8',
            )

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / 'check_run_legit.py'),
                    '--work', str(work), '--image', str(image),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )

        self.assertEqual(2, result.returncode)
        self.assertIn('.work/helper.py', result.stdout)

    def test_extensionless_shebang_runtime_code_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            directory = Path(temp_dir)
            work = directory / '.work'
            work.mkdir()
            (work / 'bulk-generator').write_text(
                '#!/usr/bin/env python3\nprint("generated")\n', encoding='utf-8',
            )
            image = directory / 'image.txt'
            image.write_text(
                '--- SCENE 001 ---\n'
                'Camera: wide\nStory DNA: grounded\nSetting: courtyard\n'
                'Composition: foreground and background\nSubject: Lan\n'
                'Action / Energy: walking\nStyle: painted\n'
                'Lighting / Color: daylight\nAtmosphere: quiet\nNegative: logo\n',
                encoding='utf-8',
            )

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / 'check_run_legit.py'),
                    '--work', str(work), '--image', str(image),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )

        self.assertEqual(2, result.returncode)
        self.assertIn('.work/bulk-generator', result.stdout)


class CrossCliContractTests(unittest.TestCase):
    def test_command_and_adapters_lock_parent_only_image_default(self):
        command = (ROOT / 'commands' / 'visual-prompt.toml').read_text(encoding='utf-8')
        codex = (
            ROOT / 'adapters' / 'codex' / 'visual-prompt' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        claude = (
            ROOT / 'adapters' / 'claude-code' / 'visual-prompt' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        self.assertIn('grounded + image-only', command)
        self.assertIn('Mỗi micro-batch tối đa 3', command)
        self.assertIn('video_enabled = false', command)
        self.assertIn('music_enabled = false', command)
        self.assertIn('source_anchor: <exact scene_row.source_anchor>', command)
        self.assertNotIn('PARALLEL EXPANSION', command)
        self.assertNotIn('Mặc định parallelism', command)
        self.assertIn('Never use subagents', codex)
        self.assertIn('disable-model-invocation: true', claude)
        self.assertIn('at most three', codex)
        self.assertIn('at most three', claude)

    def test_depth_rules_do_not_force_unsupported_story_details(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        expander = (
            ROOT / 'prompts' / 'prompt-expander-image.md'
        ).read_text(encoding='utf-8')
        template = (
            ROOT / 'references' / 'visual-prompt-template.md'
        ).read_text(encoding='utf-8')
        bible_extractor = (
            ROOT / 'prompts' / 'bible-extractor.md'
        ).read_text(encoding='utf-8')

        self.assertNotIn('engaged in meaningful action', skill)
        self.assertIn('truthful stillness', skill)
        self.assertIn('HALT instead of padding', expander)
        self.assertIn('STRUCTURE ONLY, NEVER A CONTENT DEFAULT', template)
        self.assertNotIn('estimate if not stated', bible_extractor)
        self.assertIn('unknown values are exactly `not stated`', bible_extractor)


class BatchResumeTests(unittest.TestCase):
    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_skip_requires_matching_completion_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            base = Path(temp_dir)
            folder = base / 'novel'
            folder.mkdir()
            chapter = folder / 'chapter-001.txt'
            chapter.write_text('Chương 1. Test\n', encoding='utf-8')
            stem = chapter.with_suffix('')
            image = Path(f'{stem}_image_prompts.txt')
            music = Path(f'{stem}_music_prompts.txt')
            qa = Path(f'{stem}_qa.txt')
            for path, text in ((image, 'image\n'), (music, 'music\n'), (qa, 'qa\n')):
                path.write_text(text, encoding='utf-8')
            cache = Path(f'{stem}_music-cache')
            cache.mkdir()
            plan = cache / 'music-plan.md'
            region = cache / 'music-001.md'
            plan.write_text('plan\n', encoding='utf-8')
            region.write_text('region\n', encoding='utf-8')
            version = json.loads((ROOT / 'gemini-extension.json').read_text())['version']
            manifest = Path(f'{stem}_visual-prompt-complete.json')
            manifest.write_text(json.dumps({
                'schema': 1,
                'skill_version': version,
                'series': 'safe-series',
                'style': '',
                'model': 'Gemini 3.1 Pro (High)',
                'music_n': 1,
                'no_video': True,
                'artifacts': {
                    'input': self._digest(chapter),
                    'image': self._digest(image),
                    'music': self._digest(music),
                    'qa': self._digest(qa),
                    'music_plan': self._digest(plan),
                    'music_regions': [self._digest(region)],
                },
            }), encoding='utf-8')
            environment = os.environ.copy()
            environment.update({
                'HOME': str(base / 'home'),
                'VP_DRYRUN': '1',
                'VP_MUSIC': '1',
                'VP_NO_VIDEO': '1',
                'VP_SERIES': 'safe-series',
                'VP_LOCAL': str(base / 'local'),
            })

            skipped = subprocess.run(
                ['bash', str(SCRIPTS / 'run-folder.sh'), str(folder)],
                cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
            )
            image.write_text('mutated image\n', encoding='utf-8')
            rerun = subprocess.run(
                ['bash', str(SCRIPTS / 'run-folder.sh'), str(folder)],
                cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
            )

        self.assertEqual(0, skipped.returncode, skipped.stderr)
        self.assertIn('đã có output, skip', skipped.stdout)
        self.assertEqual(0, rerun.returncode, rerun.stderr)
        self.assertNotIn('đã có output, skip', rerun.stdout)
        self.assertIn('DRYRUN:', rerun.stdout)


if __name__ == '__main__':
    unittest.main()
