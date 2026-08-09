#!/usr/bin/env python3
"""Integration contracts for template rejection and Agy runner wiring."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGIT = ROOT / 'scripts' / 'check_run_legit.py'


class TemplateJunkGateTests(unittest.TestCase):
    def test_numbered_padding_cannot_fake_prompt_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / '.work'; work.mkdir()
            (work / 'scene-plan.md').write_text('| 1 | chapter | anchored beat |\n', encoding='utf-8')
            (work / 'scene-001.md').write_text('active scene artifact\n', encoding='utf-8')
            image = root / 'image.txt'
            fields = ('Camera', 'Story DNA', 'Setting', 'Composition', 'Subject',
                      'Action / Energy', 'Style', 'Lighting / Color', 'Atmosphere', 'Negative')
            body = '\n'.join(
                f'{field}: detail{index} perspective{index} texture{index} rhythm{index}'
                for index, field in enumerate(fields)
            )
            padding = ' '.join(f'word{index}' for index in range(400))
            image.write_text(f'--- SCENE 1 ---\n{body}\nPadding: {padding}\n', encoding='utf-8')
            result = subprocess.run([
                sys.executable, str(LEGIT), '--work', str(work), '--image', str(image),
            ], text=True, capture_output=True, check=False)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn('padding', result.stdout.lower())


class IntegrationContractTests(unittest.TestCase):
    def test_plugin_and_runner_enable_the_guard_without_disabling_workers(self):
        hooks = (ROOT / 'hooks.json').read_text(encoding='utf-8')
        workspace_hooks = (ROOT / '.agents' / 'hooks.json').read_text(encoding='utf-8')
        agent = (ROOT / 'agents' / 'visual-prompt-writer' / 'agent.md').read_text(encoding='utf-8')
        runner = (ROOT / 'scripts' / 'run-folder.sh').read_text(encoding='utf-8')
        self.assertIn('active_model_guard.py', hooks)
        self.assertIn('../scripts/active_model_guard.py', workspace_hooks)
        self.assertIn('mainAgent: true', agent)
        self.assertIn('subagent: false', agent)
        self.assertIn("'--agent', 'visual-prompt-writer'", runner)
        self.assertIn("'--sandbox'", runner)
        self.assertNotIn("'--dangerously-skip-permissions'", runner)
        self.assertIn('VP_WORKERS', runner)
        self.assertIn('--require-authorship', runner)
        self.assertIn("('.agents', 'scripts', 'prompts', 'references')", runner)


if __name__ == '__main__':
    unittest.main()
