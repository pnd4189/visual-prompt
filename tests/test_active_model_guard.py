#!/usr/bin/env python3
"""Regression tests for Agy active-model authorship enforcement."""
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
GUARD = ROOT / 'scripts' / 'active_model_guard.py'
LEGIT = ROOT / 'scripts' / 'check_run_legit.py'


def run_guard(event: str, payload: dict, env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(GUARD), event], input=json.dumps(payload),
        text=True, capture_output=True, env={**os.environ, **env}, check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def base_payload(conversation: str, artifact_dir: Path) -> dict:
    return {
        'conversationId': conversation,
        'workspacePaths': [str(artifact_dir.parent)],
        'transcriptPath': str(artifact_dir / 'transcript.jsonl'),
        'artifactDirectoryPath': str(artifact_dir),
        'modelName': 'gemini-test',
    }


class ActiveModelHookTests(unittest.TestCase):
    def test_inactive_hook_does_not_affect_other_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = base_payload('unrelated', Path(tmp) / 'artifact')
            payload['toolCall'] = {'name': 'invoke_subagent', 'args': {}}
            result = run_guard('pre-tool-use', payload, {})
        self.assertEqual('allow', result['decision'])

    def test_active_primary_denies_delegation_and_runtime_generators(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / 'artifact'
            work = root / '.work'
            artifact.mkdir(); work.mkdir()
            env = {
                'VP_GUARD_ACTIVE': '1',
                'VP_GUARD_STATE': str(root / 'guard.json'),
                'VP_AUTHORSHIP_LOG': str(work / 'authorship.jsonl'),
                'VP_ALLOWED_WRITE_ROOTS': str(work),
            }
            claimed = run_guard(
                'pre-invocation', {**base_payload('primary', artifact), 'invocationNum': 0}, env,
            )
            self.assertIn('injectSteps', claimed)

            cases = [
                ('invoke_subagent', {}, 'delegation'),
                ('manage_task', {'Action': 'list'}, 'background'),
                ('write_to_file', {
                    'TargetFile': str(work / 'generate.py'),
                    'CodeContent': 'print("template")',
                }, 'runtime code'),
                ('run_command', {
                    'CommandLine': 'python3 -c "open(\'scene-001.md\', \'w\').write(\'x\')"',
                    'Cwd': str(root),
                }, 'runtime generator'),
            ]
            for tool, args, reason in cases:
                with self.subTest(tool=tool):
                    payload = {**base_payload('primary', artifact),
                               'toolCall': {'name': tool, 'args': args}}
                    result = run_guard('pre-tool-use', payload, env)
                    self.assertEqual('deny', result['decision'])
                    self.assertIn(reason, result['reason'].lower())

    def test_marker_activated_guard_fails_closed_when_state_is_corrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = root / 'artifact'; work = root / '.work'
            artifact.mkdir(); work.mkdir()
            (artifact / 'transcript.jsonl').write_text(
                'VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1\n', encoding='utf-8',
            )
            (artifact / '.visual-prompt-primary.json').write_text(
                'not-json\n', encoding='utf-8',
            )
            payload = {**base_payload('primary', artifact), 'toolCall': {
                'name': 'write_to_file', 'args': {
                    'TargetFile': str(work / 'scene-001.md'), 'CodeContent': 'scene',
                }}}
            result = run_guard('pre-tool-use', payload, {})
            self.assertEqual('deny', result['decision'])
            self.assertIn('failed closed', result['reason'])

    def test_marker_activation_persists_after_long_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = root / 'artifact'; artifact.mkdir()
            transcript = artifact / 'transcript.jsonl'
            transcript.write_text(
                'VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1\n', encoding='utf-8',
            )
            payload = {**base_payload('primary', artifact), 'invocationNum': 0}
            run_guard('pre-invocation', payload, {})
            transcript.write_text(
                'VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1\n' + ('x' * 300_000),
                encoding='utf-8',
            )
            payload = {**base_payload('primary', artifact), 'toolCall': {
                'name': 'invoke_subagent', 'args': {},
            }}
            result = run_guard('pre-tool-use', payload, {})
            self.assertEqual('deny', result['decision'])
            self.assertIn('delegation', result['reason'])

    def test_only_primary_conversation_can_mutate_and_canonical_helper_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = root / 'artifact'; work = root / '.work'
            artifact.mkdir(); work.mkdir()
            env = {'VP_GUARD_ACTIVE': '1', 'VP_GUARD_STATE': str(root / 'guard.json'),
                   'VP_AUTHORSHIP_LOG': str(work / 'authorship.jsonl'),
                   'VP_ALLOWED_WRITE_ROOTS': str(work)}
            run_guard('pre-invocation', {
                **base_payload('primary', artifact), 'invocationNum': 0,
            }, env)
            child_write = {**base_payload('child', artifact), 'toolCall': {
                'name': 'write_to_file', 'args': {
                    'TargetFile': str(work / 'scene-001.md'), 'CodeContent': 'scene',
                }}}
            self.assertEqual('deny', run_guard('pre-tool-use', child_write, env)['decision'])

            helper = {**base_payload('primary', artifact), 'toolCall': {
                'name': 'run_command', 'args': {
                    'CommandLine': 'python3 scripts/validate_artifacts.py --check scenes '
                                   '--work-dir .work --scene-plan .work/scene-plan.md',
                    'Cwd': str(ROOT),
                }}}
            self.assertEqual('allow', run_guard('pre-tool-use', helper, env)['decision'])

    def test_successful_primary_scene_write_records_content_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = root / 'artifact'; work = root / '.work'
            artifact.mkdir(); work.mkdir()
            state = root / 'guard.json'; log = work / 'authorship.jsonl'
            env = {'VP_GUARD_ACTIVE': '1', 'VP_GUARD_STATE': str(state),
                   'VP_AUTHORSHIP_LOG': str(log), 'VP_ALLOWED_WRITE_ROOTS': str(work)}
            run_guard('pre-invocation', {
                **base_payload('primary', artifact), 'invocationNum': 0,
            }, env)
            scene = work / 'scene-001.md'; scene.write_text('fresh scene', encoding='utf-8')
            payload = {**base_payload('primary', artifact), 'error': '', 'toolCall': {
                'name': 'write_to_file', 'args': {
                    'TargetFile': str(scene), 'CodeContent': 'fresh scene',
                }}}
            self.assertEqual({}, run_guard('post-tool-use', payload, env))
            self.assertEqual({}, run_guard('post-tool-use', payload, env))
            records = log.read_text(encoding='utf-8').splitlines()
            self.assertEqual(1, len(records))
            record = json.loads(records[0])
            self.assertEqual('creative_write', record['event'])
            self.assertEqual('primary', record['conversation_id'])
            self.assertEqual(hashlib.sha256(scene.read_bytes()).hexdigest(), record['sha256'])


class AuthorshipGateTests(unittest.TestCase):
    def run_worker_gate(self, root: Path, record: dict | None) -> subprocess.CompletedProcess[str]:
        work = root / 'worker'; work.mkdir()
        scene = work / 'scene-001.md'; scene.write_text('scene body', encoding='utf-8')
        manifest = root / 'manifest.json'
        manifest.write_text(json.dumps({'scene_ids': ['001']}), encoding='utf-8')
        log = root / 'authorship.jsonl'
        if record is not None:
            payload = {
                'schema': 1, 'event': 'creative_write', 'conversation_id': 'primary',
                'primary_conversation_id': 'primary', 'model': 'gemini-test',
                'tool': 'write_to_file', 'target': str(scene), 'basename': scene.name,
                'sha256': hashlib.sha256(scene.read_bytes()).hexdigest(),
                'size': scene.stat().st_size,
            }
            payload.update(record)
            log.write_text(json.dumps(payload) + '\n', encoding='utf-8')
        return subprocess.run([
            sys.executable, str(LEGIT), '--work', str(work),
            '--worker-manifest', str(manifest), '--require-authorship',
            '--authorship-log', str(log),
        ], text=True, capture_output=True, check=False)

    def test_gate_accepts_only_matching_primary_scene_provenance(self):
        cases = ((None, 2), ({}, 0), ({'sha256': '0' * 64}, 2),
                 ({'conversation_id': 'child'}, 2))
        for record, expected in cases:
            with self.subTest(record=record), tempfile.TemporaryDirectory() as tmp:
                result = self.run_worker_gate(Path(tmp), record)
                self.assertEqual(expected, result.returncode, result.stdout + result.stderr)

    def test_stale_log_does_not_force_authorship_on_other_clis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / '.work'; work.mkdir()
            (work / 'scene-plan.md').write_text(
                '| 1 | chapter | grounded beat |\n', encoding='utf-8',
            )
            (work / 'scene-001.md').write_text('scene body', encoding='utf-8')
            (work / 'active-model-authorship.jsonl').write_text(
                '{"stale": true}\n', encoding='utf-8',
            )
            image = root / 'novel_image_prompts.txt'
            image.write_text(
                '--- SCENE 001 ---\nCamera: close frame\nStory DNA: grounded beat\n'
                'Setting: quiet room\nComposition: layered depth\nSubject: lone traveler\n'
                'Action / Energy: opens a letter\nStyle: painted realism\n'
                'Lighting / Color: cool window light\nAtmosphere: restrained concern\n'
                'Negative: no logos, no text\n', encoding='utf-8',
            )
            result = subprocess.run([
                sys.executable, str(LEGIT), '--work', str(work),
                '--image', str(image),
            ], text=True, capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
