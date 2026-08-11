#!/usr/bin/env python3
"""Unit tests for Agy write-root discovery."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import active_model_policy as policy


class WriteRootTests(unittest.TestCase):
    def test_launcher_directory_fills_empty_agy_workspace_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            launch_dir = Path(tmp).resolve()
            with patch.object(policy, '_agy_launcher_cwd', return_value=launch_dir):
                self.assertEqual([launch_dir], policy.roots({'workspacePaths': []}))

    def test_explicit_runner_roots_override_launcher_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            explicit = Path(tmp).resolve()
            with patch.dict(os.environ, {'VP_ALLOWED_WRITE_ROOTS': str(explicit)}), \
                    patch.object(policy, '_agy_launcher_cwd') as launcher:
                self.assertEqual([explicit], policy.roots({'workspacePaths': []}))
                launcher.assert_not_called()

    def test_direct_fallback_allows_work_artifacts_but_not_source_files(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(policy, '_agy_launcher_cwd', return_value=Path(tmp).resolve()):
            root = Path(tmp).resolve()
            (root / '.work').mkdir(parents=True, exist_ok=True)
            (root / '.work' / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
            scene = root / '.work' / 'scene-001.md'
            source = root / 'novel.txt'
            self.assertIsNone(policy.write_denial(
                {'TargetFile': str(scene)}, {'workspacePaths': []},
            ))
            self.assertIn('outside', policy.write_denial(
                {'TargetFile': str(source)}, {'workspacePaths': []},
            ))

    def test_hook_cwd_is_cross_platform_fallback_when_launcher_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(policy, '_agy_launcher_cwd', return_value=None), \
                patch.object(policy, '_hook_workspace_cwd', return_value=Path(tmp).resolve()):
            self.assertEqual(
                [Path(tmp).resolve()], policy.roots({'workspacePaths': []}),
            )


class InputRootLearningTests(unittest.TestCase):
    """A direct /visual-prompt runs from whatever workspace Agy has open."""

    def test_first_helper_call_opens_the_input_work_dir_and_nothing_more(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as novel:
            workspace, novel_dir = Path(tmp).resolve(), Path(novel).resolve()
            (novel_dir / 'chuong.txt').write_text('x', encoding='utf-8')
            payload = {'workspacePaths': [str(workspace)],
                       'artifactDirectoryPath': str(workspace)}
            (novel_dir / '.work').mkdir(exist_ok=True)
            (novel_dir / '.work' / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
            scene = novel_dir / '.work' / 'scene-001.md'
            env = {'VP_GUARD_STATE': str(workspace / 'guard.json')}
            with patch.dict(os.environ, env), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=workspace):
                self.assertIn('outside the guarded artifact roots',
                              policy.write_denial({'TargetFile': str(scene)}, payload))
                self.assertIsNone(policy.command_denial({
                    'CommandLine': f'python3 {ROOT}/scripts/load_input.py '
                                   f'{novel_dir}/chuong.txt',
                    'Cwd': str(workspace),
                }, payload))
                self.assertIsNone(policy.write_denial({'TargetFile': str(scene)}, payload))
                # The folder itself stays closed — only .work/ opens up.
                self.assertIn('outside the guarded artifact roots', policy.write_denial(
                    {'TargetFile': str(novel_dir / 'stray.md')}, payload,
                ))

    def test_a_later_helper_cannot_repoint_the_learned_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as first, \
                tempfile.TemporaryDirectory() as second:
            workspace = Path(tmp).resolve()
            one, two = Path(first).resolve(), Path(second).resolve()
            (one / 'a.txt').write_text('x', encoding='utf-8')
            (two / 'b.txt').write_text('y', encoding='utf-8')
            payload = {'workspacePaths': [str(workspace)],
                       'artifactDirectoryPath': str(workspace)}
            with patch.dict(os.environ, {'VP_GUARD_STATE': str(workspace / 'guard.json')}), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=workspace):
                for folder, name in ((one, 'a.txt'), (two, 'b.txt')):
                    policy.command_denial({
                        'CommandLine': f'python3 {ROOT}/scripts/load_input.py '
                                       f'{folder}/{name}',
                        'Cwd': str(workspace),
                    }, payload)
                (one / '.work').mkdir(exist_ok=True)
                (one / '.work' / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
                self.assertIsNone(policy.write_denial(
                    {'TargetFile': str(one / '.work' / 'scene-001.md')}, payload,
                ))
                self.assertIn('outside the guarded artifact roots', policy.write_denial(
                    {'TargetFile': str(two / '.work' / 'scene-001.md')}, payload,
                ))


class CommandPolicyTests(unittest.TestCase):
    def denial(self, command: str, root: Path) -> str | None:
        env = {
            'VP_ALLOWED_WRITE_ROOTS': str(root / '.work'),
            'VP_ALLOWED_OUTPUT_ROOTS': str(root),
            'VP_AUTHORSHIP_LOG': str(root / '.work' / 'active-model-authorship.jsonl'),
        }
        args = {'CommandLine': command, 'Cwd': str(ROOT)}
        payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
        with patch.dict(os.environ, env):
            return policy.command_denial(args, payload)

    def test_unquoted_absolute_helper_path_with_spaces_still_resolves(self):
        # The installed skill root contains a space, so an unquoted absolute
        # helper call must not be mistaken for a rogue script.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            helper = f'{ROOT}/scripts/load_input.py'
            self.assertIsNone(self.denial(f'python3 {helper} {root}/novel.txt', root))
            self.assertIsNone(self.denial(f'python3 "{helper}" {root}/novel.txt', root))
            rogue = self.denial(f'python3 {ROOT}/scripts/generate_scenes.py', root)
            self.assertIn('canonical', rogue)

    def test_mirrored_install_helper_is_accepted_only_while_byte_identical(self):
        # Windows setup.bat copies the skill when symlinks are unavailable, so a
        # helper may legitimately run from another prefix — but only unmodified.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            mirror = root / 'skill-copy' / 'scripts'
            mirror.mkdir(parents=True)
            canonical = ROOT / 'scripts' / 'load_input.py'
            mirrored = mirror / 'load_input.py'
            mirrored.write_bytes(canonical.read_bytes())
            self.assertIsNone(self.denial(f'python3 {mirrored} {root}/novel.txt', root))
            mirrored.write_bytes(canonical.read_bytes() + b'\n# injected\n')
            self.assertIn('canonical', self.denial(f'python3 {mirrored}', root))

    def test_helper_owned_scratch_cannot_be_hand_written_but_helpers_still_emit_it(self):
        # Hand-writing chapters_qa.json skips assemble_qa.py, which is what also
        # emits <stem>_qa.txt — the run then fails the driver's output check and
        # costs a whole retry.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); work = root / '.work'; work.mkdir()
            payload = {'workspacePaths': [str(root)]}
            with patch.dict(os.environ, {'VP_ALLOWED_WRITE_ROOTS': str(work)}):
                for name in ('chapters.json', 'chapters_qa.json'):
                    with self.subTest(name=name):
                        self.assertIn('canonical helper', policy.write_denial(
                            {'TargetFile': str(work / name)}, payload,
                        ))
            # The helper's own redirect into that same file must still pass.
            self.assertIsNone(self.denial(
                f'python3 {ROOT}/scripts/load_input.py {root}/novel.txt '
                f'> {work}/chapters.json', root,
            ))

    def test_code_disguised_as_a_text_artifact_is_denied(self):
        # Observed 2026-08-09: blocked from writing .py, the model wrote the same
        # program into .work/fix.md and asked the user to run it.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); work = root / '.work'; work.mkdir()
            payload = {'workspacePaths': [str(root)]}
            with patch.dict(os.environ, {'VP_ALLOWED_WRITE_ROOTS': str(work)}):
                script = ('import re\n\npath = "/x"\nwith open(path) as handle:\n'
                          '    pass\n')
                self.assertIn('disguised', policy.write_denial(
                    {'TargetFile': str(work / 'fix.md'), 'CodeContent': script}, payload,
                ))
                # Cinematography prose that merely uses those words stays writable.
                (work / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
                prose = ('Setting: a courtyard where the rain imports nothing and the '
                         'def of loyalty is tested, camera opening on a lone figure.\n')
                self.assertIsNone(policy.write_denial(
                    {'TargetFile': str(work / 'scene-001.md'), 'CodeContent': prose}, payload,
                ))

    def test_wholesale_scene_deletion_after_assembly_needs_the_cleanup_helper(self):
        # Deleting the merged scenes by hand skips cleanup_work.py's similarity
        # check — the shortcut that once left a run unable to repair itself.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); work = root / '.work'; work.mkdir()
            for number in range(1, 31):
                (work / f'scene-{number:03d}.md').write_text('body', encoding='utf-8')
            payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
            wholesale = f'rm -f {work}/scene-*.md'
            one_scene = f'rm -f {work}/scene-005.md'
            with patch.object(policy, '_agy_launcher_cwd', return_value=root):
                # Before assembly this is just --force-redo clearing the way.
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': wholesale, 'Cwd': str(root)}, payload))
                (root / 'novel_image_prompts.txt').write_text('--- SCENE 001 ---\n',
                                                              encoding='utf-8')
                self.assertIn('cleanup_work.py', policy.command_denial(
                    {'CommandLine': wholesale, 'Cwd': str(root)}, payload))
                # The repair loop keeps working on individual scenes.
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': one_scene, 'Cwd': str(root)}, payload))

    def test_canonical_helper_cannot_write_guard_config_or_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            targets = (
                ROOT / 'scripts' / 'active_model_policy.py',
                root / '.work' / 'active-model-authorship.jsonl',
                ROOT / '.agents' / 'hooks.json',
            )
            for target in targets:
                with self.subTest(target=target):
                    command = (
                        f'python3 scripts/append_bible_row.py --bible "{target}" '
                        "--row '| name | value |'"
                    )
                    self.assertIsNotNone(self.denial(command, root))

    def test_guarded_gate_requires_provenance_and_fixed_similarity_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            gate = (
                'python3 scripts/check_run_legit.py --work .work '
                '--image novel_image_prompts.txt'
            )
            similarity = (
                'python3 scripts/check_prompt_similarity.py '
                '--image novel_image_prompts.txt --max-pair-copies 99'
            )
            self.assertIn('provenance', self.denial(gate, root))
            self.assertIn('immutable', self.denial(similarity, root))

    def test_legitimate_helpers_remain_allowed_but_provenance_glob_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); work = root / '.work'; work.mkdir()
            (work / 'active-model-authorship.jsonl').write_text('{}\n', encoding='utf-8')
            bible = work / 'character-bible.md'
            novel = root / 'novel.txt'
            append = (
                f'python3 scripts/append_bible_row.py --bible "{bible}" '
                "--row '| Lan | calm; watchful |'"
            )
            assemble = (
                f'python3 scripts/assemble_outputs.py --input "{novel}" '
                f'--work-dir "{work}"'
            )
            self.assertIsNone(self.denial(append, root))
            self.assertIsNone(self.denial(assemble, root))
            self.assertIn('immutable', self.denial(f'rm -f "{work}"/*', root))

    def test_shell_background_and_helper_path_expansion_are_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            background = (
                'python3 scripts/validate_artifacts.py --check scenes '
                '--work-dir .work & python3 forbidden.py'
            )
            expanded_report = (
                'python3 scripts/check_run_legit.py --work .work '
                '--image novel_image_prompts.txt --require-authorship '
                '--authorship-log .work/active-model-authorship.jsonl '
                '--report-json .work/*.json'
            )
            self.assertIn('composition', self.denial(background, root))
            self.assertIn('expansion', self.denial(expanded_report, root))

class LeanSpecTests(unittest.TestCase):
    """--lean swaps the prompt contract; the model must not pick the mode."""

    def _state(self, root: Path, lean: bool) -> dict:
        (root / 'guard.json').write_text(json.dumps({
            'schema': 1, 'primary_conversation_id': 'primary', 'lean': lean,
        }), encoding='utf-8')
        return {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}

    def test_the_model_cannot_choose_the_prompt_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            (root / 'novel.txt').write_text('x', encoding='utf-8')
            command = (f'python3 {ROOT}/scripts/assemble_outputs.py '
                       f'--input {root}/novel.txt')
            with patch.dict(os.environ, {'VP_GUARD_STATE': str(root / 'guard.json')}), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=root):
                deep = self._state(root, lean=False)
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': command, 'Cwd': str(root)}, deep))
                self.assertIn('was not requested', policy.command_denial(
                    {'CommandLine': command + ' --lean', 'Cwd': str(root)}, deep))

                lean = self._state(root, lean=True)
                self.assertIn('must be called with --lean', policy.command_denial(
                    {'CommandLine': command, 'Cwd': str(root)}, lean))
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': command + ' --lean', 'Cwd': str(root)}, lean))


class PlanGateMustPassFirstTests(unittest.TestCase):
    """A failed gate means HALT; the model kept expanding anyway."""

    def _denial(self, root: Path, worker: bool = False):
        (root / 'guard.json').write_text(json.dumps({
            'schema': 1, 'primary_conversation_id': 'primary', 'worker': worker,
        }), encoding='utf-8')
        payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
        with patch.dict(os.environ, {'VP_GUARD_STATE': str(root / 'guard.json')}), \
                patch.object(policy, '_agy_launcher_cwd', return_value=root):
            return policy.write_denial(
                {'TargetFile': str(root / '.work' / 'scene-001.md')}, payload)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / '.work').mkdir()
        self.addCleanup(self._tmp.cleanup)

    def test_scenes_are_refused_while_the_plan_gate_is_failing(self):
        """Observed 2026-08-11: 77 scenes written on a plan with 26 invented
        anchors and 42 invented characters, because exit 2 did not stop it."""
        denial = self._denial(self.root)

        self.assertIn('plan.hash', denial)
        self.assertIn('exits 0', denial)

    def test_scenes_flow_once_the_gate_has_passed(self):
        (self.root / '.work' / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')

        self.assertIsNone(self._denial(self.root))

    def test_a_worker_starts_at_expansion_by_design(self):
        """Pass-2 workers skip STEP 1-5 and keep the plan in a frozen snapshot."""
        self.assertIsNone(self._denial(self.root, worker=True))


class LeanSceneShapeTests(unittest.TestCase):
    """A lean scene written as prose has no fields for the repetition gate."""

    FLAT = ('---\nscene_id: "001"\n---\n## Image Prompt\n'
            'high-end donghua render, inside a military tent at dusk, '
            'he glances at her and says nothing.\n')
    SHAPED = ('---\nscene_id: "001"\n---\n## Image Prompt\n\n'
              'Subject: Phac Minh, tall, dark robes\n'
              'Setting: inside the military tent at Luoshui, canvas dim at dusk\n'
              'Action: he glances at her once and keeps his silence\n'
              'Style: donghua-xianxia\nNegative: no logo, no watermark\n')

    def _denial(self, root, body, tool, lean):
        (root / 'guard.json').write_text(json.dumps({
            'schema': 1, 'primary_conversation_id': 'primary', 'lean': lean,
        }), encoding='utf-8')
        payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
        args = {'TargetFile': str(root / '.work' / 'scene-001.md'), 'CodeContent': body}
        with patch.dict(os.environ, {'VP_GUARD_STATE': str(root / 'guard.json')}), \
                patch.object(policy, '_agy_launcher_cwd', return_value=root):
            return policy.write_denial(args, payload, tool=tool)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / '.work').mkdir()
        (self.root / '.work' / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
        self.addCleanup(self._tmp.cleanup)

    def test_a_flattened_lean_scene_is_refused(self):
        denial = self._denial(self.root, self.FLAT, 'write_to_file', True)

        self.assertIn('lean prompt spec', denial)
        self.assertIn('Setting', denial)

    def test_a_properly_fielded_lean_scene_passes(self):
        self.assertIsNone(
            self._denial(self.root, self.SHAPED, 'write_to_file', True))

    def test_a_partial_edit_is_never_judged_on_shape(self):
        """The repair itself arrives as a fragment; blocking it would deadlock."""
        self.assertIsNone(
            self._denial(self.root, 'Setting: a tent at dusk in the rain',
                         'replace_file_content', True))

    def test_a_stub_field_is_refused_as_it_is_written(self):
        """"living room" passed the shape check and only failed a gate later.

        validate_artifacts measures the same range, but only when the model runs
        it, and three runs in a row wrote hundreds of scenes without doing so.
        """
        stub = self.SHAPED.replace(
            'Setting: inside the military tent at Luoshui, canvas dim at dusk',
            'Setting: living room')

        denial = self._denial(self.root, stub, 'write_to_file', True)

        self.assertIn('lean Setting has 2 word(s)', denial)

    def test_a_field_long_enough_to_eat_the_prompt_is_refused(self):
        bloated = self.SHAPED.replace(
            'Action: he glances at her once and keeps his silence',
            'Action: ' + ' '.join(['từ'] * 45))

        self.assertIn('45 word(s)',
                      self._denial(self.root, bloated, 'write_to_file', True))

    def test_the_deep_spec_is_not_held_to_the_lean_fields(self):
        self.assertIsNone(self._denial(self.root, self.FLAT, 'write_to_file', False))

    def test_fields_without_the_heading_are_refused(self):
        """Observed 2026-08-11: 300 scenes, all five fields, no frontmatter at all.

        The gate could not bind any of them to a plan row, so all 300 needed
        rewriting after the fact.
        """
        headless = self.SHAPED.split('## Image Prompt', 1)[1].lstrip()

        denial = self._denial(self.root, headless, 'write_to_file', True)

        self.assertIn('## Image Prompt', denial)
        self.assertIn('cache_key', denial)


class PlanNeedsQaSourceTests(unittest.TestCase):
    """The plan cites QA'd chapters, so it cannot be written before they exist."""

    def test_the_shortcut_from_genre_straight_to_the_plan_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            work = root / '.work'; work.mkdir()
            payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
            plan = {'TargetFile': str(work / 'scene-plan.md')}
            env = {'VP_GUARD_STATE': str(root / 'guard.json')}

            with patch.dict(os.environ, env), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=root):
                # Observed shape: genre and style written, no QA source anywhere.
                (work / 'genre.txt').write_text('tien-hiep', encoding='utf-8')
                denial = policy.write_denial(plan, payload)
                self.assertIn('chapters_qa.json', denial)
                self.assertIn('STEP 1', denial)

                # Same write, once the QA loop has actually produced its source.
                (work / 'chapters_qa.json').write_text('[]', encoding='utf-8')
                self.assertIsNone(policy.write_denial(plan, payload))

    def test_scene_files_are_not_caught_by_the_plan_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            work = root / '.work'; work.mkdir()
            (work / 'plan.hash').write_text('0123456789ab\n', encoding='utf-8')
            payload = {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}
            env = {'VP_GUARD_STATE': str(root / 'guard.json')}

            with patch.dict(os.environ, env), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=root):
                self.assertIsNone(policy.write_denial(
                    {'TargetFile': str(work / 'scene-001.md')}, payload))


class ExpectImagesTests(unittest.TestCase):
    """The scene total is the formula's or the user's — never the model's."""

    def _state(self, root: Path, images_override) -> dict:
        (root / 'guard.json').write_text(json.dumps({
            'schema': 1, 'primary_conversation_id': 'primary',
            'images_override': images_override,
        }), encoding='utf-8')
        return {'workspacePaths': [str(root)], 'artifactDirectoryPath': str(root)}

    def test_the_model_cannot_pick_the_number_it_is_measured_against(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / '.work').mkdir()
            command = (f'python3 {ROOT}/scripts/validate_scene_plan.py '
                       f'--plan {root}/.work/scene-plan.md '
                       f'--chapters-json {root}/.work/chapters_qa.json')
            with patch.dict(os.environ, {'VP_GUARD_STATE': str(root / 'guard.json')}), \
                    patch.object(policy, '_agy_launcher_cwd', return_value=root):
                auto = self._state(root, None)
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': command, 'Cwd': str(root)}, auto))
                self.assertIn('was not requested', policy.command_denial(
                    {'CommandLine': command + ' --expect-images 114',
                     'Cwd': str(root)}, auto))

                pinned = self._state(root, 200)
                self.assertIn('must be called with --expect-images 200',
                              policy.command_denial(
                                  {'CommandLine': command, 'Cwd': str(root)}, pinned))
                self.assertIn('must be called with --expect-images 200',
                              policy.command_denial(
                                  {'CommandLine': command + ' --expect-images 114',
                                   'Cwd': str(root)}, pinned))
                self.assertIsNone(policy.command_denial(
                    {'CommandLine': command + ' --expect-images 200',
                     'Cwd': str(root)}, pinned))


if __name__ == '__main__':
    unittest.main()
