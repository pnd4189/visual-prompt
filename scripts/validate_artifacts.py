#!/usr/bin/env python3
"""Validate visual-prompt intermediate and final artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _io_utils import read_text_checked  # type: ignore
from validate_scene_plan import parse_plan_contract  # type: ignore

_ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')
_SCENE_FILE_RE = re.compile(r'^scene-(\d{3}[a-zA-Z]?)\.md$')
_MUSIC_FILE_RE = re.compile(r'^music-(\d{3,})\.md$')
_SCENE_OUTPUT_RE = re.compile(r'^--- SCENE (\d+[a-zA-Z]?) ---\s*$', re.MULTILINE)
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
_CACHE_KEY_RE = re.compile(r'^[0-9a-f]{16}$')
_MUSIC_PLAN_COLUMNS = ('loop_index', 'chapter_start', 'chapter_end', 'mood')
_MUSIC_MOODS = {
    'calm/intro', 'mystery/journey', 'tension/battle',
    'sad/reflection', 'triumph/resolution',
}
_MUSIC_ENDING = (
    'loop-ready 2-3 minute seamless background loop, no vocals, no lyrics, '
    'instrumental only.'
)
_FORBIDDEN_MUSIC_PHRASES = (
    'trailer', 'bombastic', 'pounding', 'driving beat', 'war drums',
    'aggressive', 'explosive', 'high energy', 'cymbal crashes',
    'accelerating', 'battle score',
)
_FORBIDDEN_MUSIC_TAGS = ('battle', 'trailer', 'war drums', 'aggressive', 'crescendo')


def _result(check: str, errors: list[str], **extra) -> dict:
    return {'ok': not errors, 'check': check, **extra, 'errors': errors}


def _read_nonempty(path: Path, errors: list[str], label: str) -> str | None:
    try:
        text = read_text_checked(path)
    except FileNotFoundError:
        errors.append(f'missing {label}: {path.name}')
        return None
    except (OSError, RuntimeError) as exc:
        errors.append(str(exc))
        return None
    if not text:
        errors.append(f'empty {label}: {path.name}')
        return None
    return text


def _frontmatter_fields(text: str) -> set[str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return set()
    return {
        line.split(':', 1)[0].strip()
        for line in match.group(1).splitlines()
        if ':' in line
    }


def _frontmatter_values(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    values = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key.strip()] = value
    return values


def _normalize_source(value: str) -> str:
    return ' '.join(value.casefold().split())


def _scene_filename(scene_id: str) -> str:
    match = re.fullmatch(r'(\d+)([a-zA-Z]?)', scene_id)
    if not match:
        return f'scene-{scene_id}.md'
    return f'scene-{int(match.group(1)):03d}{match.group(2).casefold()}.md'


def _music_index(filename: str) -> int:
    match = _MUSIC_FILE_RE.fullmatch(filename)
    if not match:
        raise ValueError(f'invalid music filename: {filename}')
    return int(match.group(1))


def parse_scene_plan(path: Path) -> tuple[list[str], set[str]]:
    rows, _, _ = parse_plan_contract(read_text_checked(path))
    scene_ids = [row['scene_id'].casefold() for row in rows]
    video_ids = {
        row['scene_id'].casefold()
        for row in rows
        if row['has_video']
    }
    return scene_ids, video_ids


def _scene_plan_details(
    path: Path,
) -> tuple[list[str], set[str], list[str], dict | None, dict[str, str]]:
    rows, errors, totals = parse_plan_contract(read_text_checked(path))
    scene_ids = [row['scene_id'].casefold() for row in rows]
    video_ids = {
        row['scene_id'].casefold()
        for row in rows
        if row['has_video']
    }
    anchors = {
        row['scene_id'].casefold(): row['source_anchor']
        for row in rows
    }
    return scene_ids, video_ids, errors, totals, anchors


def parse_music_plan(path: Path) -> tuple[list[dict], list[str]]:
    """Parse and validate the persisted music region table."""
    regions: list[dict] = []
    errors: list[str] = []
    header_seen = False
    for line_number, line in enumerate(read_text_checked(path).splitlines(), 1):
        match = _ROW_RE.match(line)
        cells = [cell.strip() for cell in match.group(1).split('|')] if match else []
        if not cells:
            continue
        normalized = tuple(cell.casefold() for cell in cells)
        if normalized == _MUSIC_PLAN_COLUMNS:
            header_seen = True
            continue
        if all(set(cell) <= {'-', ':'} for cell in cells):
            continue
        if not header_seen:
            if cells[0].isdigit():
                errors.append(f'{path.name}:{line_number} music row appears before schema header')
            continue
        if len(cells) != 4:
            errors.append(f'{path.name}:{line_number} music row must have 4 columns')
            continue
        try:
            loop_index = int(cells[0])
            chapter_start = int(cells[1])
            chapter_end = int(cells[2])
        except ValueError:
            errors.append(f'{path.name}:{line_number} loop/chapter values must be integers')
            continue
        mood = cells[3].casefold()
        if loop_index < 1:
            errors.append(f'{path.name}:{line_number} loop_index must be positive')
        if chapter_start < 1 or chapter_end < 1:
            errors.append(f'{path.name}:{line_number} chapter ids must be positive')
        if chapter_start > chapter_end:
            errors.append(f'{path.name}:{line_number} chapter range is reversed')
        if mood not in _MUSIC_MOODS:
            errors.append(f'{path.name}:{line_number} unsupported mood: {cells[3] or "<empty>"}')
        regions.append({
            'loop_index': loop_index,
            'chapter_start': chapter_start,
            'chapter_end': chapter_end,
            'mood': mood,
        })
    if not header_seen:
        errors.append(f'{path.name} missing music plan schema header')
    loop_ids = [region['loop_index'] for region in regions]
    if loop_ids and loop_ids != list(range(1, len(loop_ids) + 1)):
        errors.append(f'{path.name} loop_index values must be sequential from 1')
    for previous, current in zip(regions, regions[1:]):
        if current['chapter_start'] not in {
            previous['chapter_end'], previous['chapter_end'] + 1,
        }:
            errors.append(
                f"{path.name} chapter ranges must be contiguous: "
                f"{previous['chapter_end']} -> {current['chapter_start']}"
            )
    return regions, errors


def _cache_key(*parts: str) -> str:
    payload = '\0'.join(parts).encode('utf-8')
    return hashlib.sha1(payload).hexdigest()[:16]


def _region_payload(region: dict, total: int) -> str:
    return json.dumps(
        {**region, 'total': total}, ensure_ascii=False,
        sort_keys=True, separators=(',', ':'),
    )


def _chapter_coverage_errors(work_dir: Path, regions: list[dict]) -> list[str]:
    chapters_path = work_dir / 'chapters_qa.json'
    if not chapters_path.exists():
        return [f'missing chapter source for music plan: {chapters_path.name}']
    if not regions:
        return []
    try:
        chapters = json.loads(read_text_checked(chapters_path))
        chapter_ids = [int(chapter['id']) for chapter in chapters]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError, RuntimeError) as exc:
        return [f'cannot validate music plan against {chapters_path.name}: {exc}']
    if len(chapter_ids) != len(set(chapter_ids)):
        return [f'{chapters_path.name} contains duplicate chapter ids']
    if not chapter_ids or any(
        current != previous + 1
        for previous, current in zip(chapter_ids, chapter_ids[1:])
    ):
        return [f'{chapters_path.name} chapter ids must be ordered and contiguous']
    if any(
        region['chapter_start'] < chapter_ids[0]
        or region['chapter_end'] > chapter_ids[-1]
        for region in regions
    ):
        return ['music plan chapter range falls outside the chapter source']
    if len(regions) <= len(chapter_ids):
        for previous, current in zip(regions, regions[1:]):
            if current['chapter_start'] <= previous['chapter_end']:
                return ['music plan chapter ranges overlap unnecessarily']
    covered = {
        chapter_id
        for region in regions
        for chapter_id in range(region['chapter_start'], region['chapter_end'] + 1)
    }
    if sorted(covered) != chapter_ids:
        return [f'music plan chapter coverage does not match {chapters_path.name}']
    return []


def _music_body_errors(body: str) -> list[str]:
    errors: list[str] = []
    chunks = [chunk.strip() for chunk in re.split(r'\n\s*\n', body.strip()) if chunk.strip()]
    tag_matches = re.findall(r'^Tags:', body, re.MULTILINE | re.IGNORECASE)
    if len(chunks) != 2 or len(tag_matches) != 1 or not chunks[-1].lower().startswith('tags:'):
        errors.append('body must contain one paragraph followed by one Tags section')
        return errors
    paragraph = ' '.join(chunks[0].split())
    word_count = len(paragraph.split())
    if not 55 <= word_count <= 85:
        errors.append(f'prompt paragraph has {word_count} words, expected 55-85')
    if not paragraph.casefold().endswith(_MUSIC_ENDING):
        errors.append('prompt paragraph has the wrong loop-ready ending')
    lowered = paragraph.casefold()
    blocked = [phrase for phrase in _FORBIDDEN_MUSIC_PHRASES if phrase in lowered]
    if blocked:
        errors.append(f'prompt paragraph contains forbidden phrase(s): {blocked}')
    tag_text = ' '.join(chunks[1].split()).split(':', 1)[1]
    tags = [tag.strip().casefold() for tag in tag_text.split(',') if tag.strip()]
    tag_count = len(tags)
    if not 12 <= tag_count <= 16:
        errors.append(f'Tags section has {tag_count} tags, expected 12-16')
    if len(tags) != len(set(tags)):
        errors.append('Tags section contains duplicate tags')
    lowered_tags = tag_text.casefold()
    blocked_tags = [tag for tag in _FORBIDDEN_MUSIC_TAGS if tag in lowered_tags]
    if blocked_tags:
        errors.append(f'Tags section contains forbidden tag(s): {blocked_tags}')
    return errors


def _split_music_output(text: str) -> tuple[list[str], bool]:
    blocks: list[str] = []
    pending: list[str] = []
    for chunk in re.split(r'\n\s*\n', text.strip()):
        if not chunk.strip():
            continue
        pending.append(chunk.strip())
        if chunk.lstrip().lower().startswith('tags:'):
            blocks.append('\n\n'.join(pending))
            pending = []
    return blocks, not pending


def check_scenes(work_dir: Path, plan_path: Path) -> dict:
    scene_ids, video_ids, plan_errors, totals, anchors = _scene_plan_details(plan_path)
    errors = [f'{plan_path.name}: {error}' for error in plan_errors]
    expected_names = [_scene_filename(scene_id) for scene_id in scene_ids]
    expected = set(expected_names)
    extra = {
        'expected': totals['images'] if totals else len(scene_ids),
        'videos_expected': totals['videos'] if totals else len(video_ids),
    }
    if not scene_ids:
        errors.append(f'no scene rows parsed from {plan_path}')
    if len(scene_ids) != len(set(scene_ids)):
        errors.append(f'{plan_path.name} contains duplicate scene ids')
    if len(expected_names) != len(expected):
        errors.append(f'{plan_path.name} contains scene id aliases')

    for scene_id in scene_ids:
        path = work_dir / _scene_filename(scene_id)
        text = _read_nonempty(path, errors, 'scene file')
        if text is None:
            return _result('scenes', errors, **extra)
        missing = {
            'scene_id', 'cache_key', 'has_video', 'source_anchor',
        } - _frontmatter_fields(text)
        if missing:
            errors.append(f'{path.name} missing frontmatter field(s): {sorted(missing)}')
        values = _frontmatter_values(text)
        if _scene_filename(values.get('scene_id', '')) != path.name:
            errors.append(f'{path.name} scene_id does not match filename/plan')
        if not _CACHE_KEY_RE.fullmatch(values.get('cache_key', '')):
            errors.append(f'{path.name} cache_key must be 16 lowercase hex characters')
        expected_has_video = scene_id in video_ids
        if values.get('has_video', '').casefold() != str(expected_has_video).casefold():
            errors.append(f'{path.name} has_video does not match scene plan')
        expected_anchor = anchors.get(scene_id, '')
        if _normalize_source(values.get('source_anchor', '')) != _normalize_source(
            expected_anchor
        ):
            errors.append(f'{path.name} source_anchor does not match scene plan')
        if '## Image Prompt' not in text:
            errors.append(f'{path.name} missing ## Image Prompt')
        if expected_has_video and '## Video Prompt' not in text:
            errors.append(f'{path.name} missing ## Video Prompt')
        if not expected_has_video and '## Video Prompt' in text:
            errors.append(f'{path.name} has unexpected ## Video Prompt')

    for path in work_dir.glob('scene-*.md'):
        if path.name == 'scene-plan.md':
            continue
        if not _SCENE_FILE_RE.fullmatch(path.name):
            errors.append(f'unexpected scene-like file: {path.name}')
        elif path.name not in expected:
            errors.append(f'unexpected scene id not in plan: {path.name}')
    return _result('scenes', errors, **extra)


def check_music(work_dir: Path, expected_music: int, music_plan: Path | None = None,
                cache_context: tuple[str, str, str, str] | None = None) -> dict:
    errors: list[str] = []
    plan_path = music_plan or work_dir / 'music-plan.md'
    expected_ids = list(range(1, expected_music + 1))
    regions: list[dict] = []
    if music_plan is not None and not plan_path.exists():
        errors.append(f'missing explicit music plan: {plan_path}')
    if plan_path.exists():
        plan_text = _read_nonempty(plan_path, errors, 'music plan')
        plan_values = _frontmatter_values(plan_text or '')
        plan_key = plan_values.get('cache_key', '')
        required_plan_fields = {
            'cache_key', 'qa_hash', 'genre', 'plan_hash', 'style_hash', 'music_n',
        }
        missing_plan_fields = required_plan_fields - plan_values.keys()
        if missing_plan_fields:
            errors.append(
                f'{plan_path.name} missing frontmatter field(s): {sorted(missing_plan_fields)}'
            )
        if not _CACHE_KEY_RE.fullmatch(plan_key):
            errors.append(f'{plan_path.name} cache_key must be 16 lowercase hex characters')
        regions, plan_errors = parse_music_plan(plan_path)
        errors.extend(plan_errors)
        errors.extend(_chapter_coverage_errors(work_dir, regions))
        expected_ids = [region['loop_index'] for region in regions]
        if not regions:
            errors.append(f'no music regions parsed from {plan_path.name}')
        if expected_music > 0 and len(regions) != expected_music:
            errors.append(
                f'{plan_path.name} has {len(regions)} regions, expected {expected_music}'
            )
        try:
            stored_music_n = int(plan_values.get('music_n', ''))
        except ValueError:
            stored_music_n = 0
            errors.append(f'{plan_path.name} music_n must be a positive integer')
        if stored_music_n != len(regions):
            errors.append(f'{plan_path.name} music_n does not match region count')
        stored_context = tuple(
            plan_values.get(field, '')
            for field in ('qa_hash', 'genre', 'plan_hash', 'style_hash')
        )
        if cache_context is None:
            for field, filename in (
                ('qa_hash', 'qa.hash'),
                ('genre', 'genre.txt'),
                ('plan_hash', 'plan.hash'),
                ('style_hash', 'style.hash'),
            ):
                try:
                    current_value = read_text_checked(work_dir / filename).strip()
                except (OSError, RuntimeError) as exc:
                    errors.append(f'cannot validate {field} from {filename}: {exc}')
                    continue
                if plan_values.get(field) != current_value:
                    errors.append(f'{plan_path.name} {field} is stale')
        effective_context = cache_context or stored_context
        if cache_context is not None and stored_context != cache_context:
            errors.append(f'{plan_path.name} cache context does not match validator input')
        if all(effective_context) and stored_music_n > 0:
            qa_hash, genre, plan_hash, _ = effective_context
            expected_plan_key = _cache_key(qa_hash, genre, plan_hash, str(stored_music_n))
            if plan_key != expected_plan_key:
                errors.append(f'{plan_path.name} cache_key is stale')
            cache_context = effective_context
        else:
            errors.append(f'{plan_path.name} cache context is incomplete')
    expected = {f'music-{idx:03d}.md' for idx in expected_ids}
    expected_count = len(expected_ids)
    for name in sorted(expected):
        text = _read_nonempty(work_dir / name, errors, 'music file')
        if text is None:
            return _result('music', errors, expected=expected_count)
        values = _frontmatter_values(text)
        missing = {
            'loop_index', 'total', 'chapter_start', 'chapter_end', 'mood', 'cache_key'
        } - values.keys()
        if missing:
            errors.append(f'{name} missing frontmatter field(s): {sorted(missing)}')
        music_index = _music_index(name)
        region = next((item for item in regions if item['loop_index'] == music_index), None)
        if not _CACHE_KEY_RE.fullmatch(values.get('cache_key', '')):
            errors.append(f'{name} cache_key must be 16 lowercase hex characters')
        if values.get('loop_index') != str(music_index):
            errors.append(f'{name} loop_index does not match filename')
        if values.get('total') != str(expected_count):
            errors.append(f'{name} total does not match expected region count')
        if region is not None:
            for field in ('chapter_start', 'chapter_end', 'mood'):
                if values.get(field, '').casefold() != str(region[field]).casefold():
                    errors.append(f'{name} {field} does not match music plan')
            if cache_context is not None:
                qa_hash, genre, plan_hash, style_hash = cache_context
                expected_key = _cache_key(
                    qa_hash, genre, plan_hash, style_hash,
                    _region_payload(region, expected_count),
                )
                if values.get('cache_key') != expected_key:
                    errors.append(f'{name} cache_key is stale')
        body = _FRONTMATTER_RE.sub('', text, count=1).strip()
        if not body:
            errors.append(f'{name} has empty body')
        for detail in _music_body_errors(body):
            errors.append(f'{name} {detail}')
        if '--- LOOP' in body or '\nNegative:' in body or '\nLoop:' in body:
            errors.append(f'{name} uses obsolete music block format')

    for path in work_dir.glob('music-*.md'):
        if path.name == 'music-plan.md':
            continue
        if not _MUSIC_FILE_RE.fullmatch(path.name):
            errors.append(f'unexpected music-like file: {path.name}')
        elif path.name not in expected:
            errors.append(f'unexpected music id not expected: {path.name}')
    return _result('music', errors, expected=expected_count)


def _check_output_file(path: Path, expected: int, errors: list[str],
                       expected_ids: list[str] | None = None) -> bool:
    text = _read_nonempty(path, errors, 'output')
    if text is None:
        return False
    output_ids = [_scene_filename(scene_id)[6:-3] for scene_id in _SCENE_OUTPUT_RE.findall(text)]
    actual = len(output_ids)
    if actual != expected:
        errors.append(f'{path.name} has {actual} blocks, expected {expected}')
    if expected_ids is not None:
        canonical_expected = [_scene_filename(scene_id)[6:-3] for scene_id in expected_ids]
        if output_ids != canonical_expected:
            errors.append(f'{path.name} scene ids/order do not match scene plan')
    return True


def check_outputs(input_path: Path, image_count: int, video_count: int, music_count: int,
                  scene_plan: Path | None = None) -> dict:
    errors: list[str] = []
    output_dir = input_path.parent
    stem = input_path.stem
    extra = {
        'image_count': image_count,
        'video_count': video_count,
        'music_count': music_count,
    }
    image_path = output_dir / f'{stem}_image_prompts.txt'
    video_path = output_dir / f'{stem}_video_prompts.txt'
    music_path = output_dir / f'{stem}_music_prompts.txt'
    image_ids = None
    video_ids = None
    if scene_plan is not None:
        parsed_image_ids, parsed_video_ids, plan_errors, _, _ = _scene_plan_details(
            scene_plan
        )
        errors.extend(f'{scene_plan.name}: {error}' for error in plan_errors)
        image_ids = parsed_image_ids
        video_ids = [scene_id for scene_id in parsed_image_ids if scene_id in parsed_video_ids]
    if not _check_output_file(image_path, image_count, errors, image_ids):
        return _result('outputs', errors, **extra)
    if video_count > 0 and not _check_output_file(video_path, video_count, errors, video_ids):
        return _result('outputs', errors, **extra)
    if music_count > 0:
        music_text = _read_nonempty(music_path, errors, 'output')
        if music_text is None:
            return _result('outputs', errors, **extra)
        music_blocks, complete = _split_music_output(music_text)
        if not complete or len(music_blocks) != music_count:
            errors.append(
                f'{music_path.name} has {len(music_blocks)} complete blocks, '
                f'expected {music_count}'
            )
        for index, body in enumerate(music_blocks, 1):
            for detail in _music_body_errors(body):
                errors.append(f'{music_path.name} block {index} {detail}')
    return _result('outputs', errors, **extra)


def merge_results(results: list[dict]) -> dict:
    errors: list[str] = []
    for result in results:
        errors.extend(result.get('errors', []))
    return {'ok': not errors, 'results': results, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate visual-prompt artifacts')
    parser.add_argument('--check', choices=['scenes', 'music', 'outputs', 'all'], required=True)
    parser.add_argument('--work-dir', default=None)
    parser.add_argument('--scene-plan', default=None)
    parser.add_argument('--music-plan', default=None)
    parser.add_argument('--input', default=None)
    parser.add_argument('--expected-music', type=int, default=0)
    parser.add_argument('--image-count', type=int, default=0)
    parser.add_argument('--video-count', type=int, default=0)
    parser.add_argument('--music-count', type=int, default=0)
    parser.add_argument('--qa-hash', default=None)
    parser.add_argument('--genre', default=None)
    parser.add_argument('--plan-hash', default=None)
    parser.add_argument('--style-hash', default=None)
    args = parser.parse_args()

    work_dir = Path(args.work_dir) if args.work_dir else None
    results: list[dict] = []
    if args.check in {'scenes', 'all'}:
        if work_dir is None:
            raise SystemExit('--work-dir is required for scene validation')
        plan = Path(args.scene_plan) if args.scene_plan else work_dir / 'scene-plan.md'
        results.append(check_scenes(work_dir, plan))
    if args.check in {'music', 'all'}:
        if work_dir is None:
            raise SystemExit('--work-dir is required for music validation')
        music_plan = Path(args.music_plan) if args.music_plan else None
        cache_values = (args.qa_hash, args.genre, args.plan_hash, args.style_hash)
        supplied = [value is not None for value in cache_values]
        if any(supplied) and not all(supplied):
            raise SystemExit(
                '--qa-hash, --genre, --plan-hash, and --style-hash must be supplied together'
            )
        cache_context = cache_values if all(supplied) else None
        results.append(check_music(
            work_dir, args.expected_music, music_plan, cache_context,
        ))
    if args.check in {'outputs', 'all'}:
        if not args.input:
            raise SystemExit('--input is required for output validation')
        scene_plan = Path(args.scene_plan) if args.scene_plan else None
        results.append(check_outputs(
            Path(args.input), args.image_count, args.video_count,
            args.music_count, scene_plan,
        ))

    result = merge_results(results)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
