#!/usr/bin/env python3
"""Tests for non-destructive Agy global hook installation."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / 'scripts' / 'install_agy_guard.py'
HOOK_NAME = 'visual-prompt-active-model-guard'


class InstallAgyGuardTests(unittest.TestCase):
    def run_installer(self, target: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([
            sys.executable, str(INSTALLER), '--repo-root', str(ROOT),
            '--target', str(target),
        ], text=True, capture_output=True, check=False)

    def test_merge_preserves_existing_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'hooks.json'
            existing = {'other-hook': {'PreInvocation': []}}
            target.write_text(json.dumps(existing), encoding='utf-8')

            first = self.run_installer(target)
            self.assertEqual(0, first.returncode, first.stderr)
            installed = json.loads(target.read_text(encoding='utf-8'))
            self.assertEqual(existing['other-hook'], installed['other-hook'])
            guard = installed[HOOK_NAME]
            commands = []
            for phase in guard.values():
                for entry in phase:
                    for hook in entry.get('hooks', [entry]):
                        commands.append(hook['command'])
            self.assertEqual(4, len(commands))
            self.assertTrue(all(len(command.split()) == 3 for command in commands))
            launcher = target.parent / 'visual-prompt-active-model-guard.py'
            self.assertTrue(launcher.is_file())
            self.assertTrue(all(str(launcher) in command for command in commands))
            for command in commands:
                executed = subprocess.run(
                    command.split(), input='{}', text=True,
                    capture_output=True, check=False,
                )
                self.assertEqual(0, executed.returncode, executed.stderr)
                self.assertTrue(executed.stdout.strip())

            before = target.read_bytes()
            second = self.run_installer(target)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(before, target.read_bytes())
            self.assertIn('already current', second.stdout)

    def test_invalid_existing_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'hooks.json'
            target.write_text('not-json\n', encoding='utf-8')
            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertEqual('not-json\n', target.read_text(encoding='utf-8'))
            self.assertFalse((target.parent / 'visual-prompt-active-model-guard.py').exists())

    def test_existing_launcher_symlink_is_replaced_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            target = directory / 'hooks.json'
            self.assertEqual(0, self.run_installer(target).returncode)
            launcher = directory / 'visual-prompt-active-model-guard.py'
            expected = launcher.read_text(encoding='utf-8')
            linked = directory / 'linked-launcher.py'
            linked.write_text(expected, encoding='utf-8')
            launcher.unlink()
            launcher.symlink_to(linked)

            result = self.run_installer(target)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(launcher.is_symlink())
            self.assertEqual(expected, launcher.read_text(encoding='utf-8'))
            self.assertEqual(expected, linked.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
