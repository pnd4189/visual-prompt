#!/usr/bin/env python3
"""Unit tests for Agy write-root discovery."""
from __future__ import annotations

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


if __name__ == '__main__':
    unittest.main()
