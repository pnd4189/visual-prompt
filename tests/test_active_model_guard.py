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


class InvocationArmingTests(unittest.TestCase):
    """Agy stores the raw user turn, not the expanded slash-command prompt."""

    USER_TURN = (
        '{"step_index":0,"source":"USER_EXPLICIT","type":"USER_INPUT",'
        '"content":"<USER_REQUEST>\\n/visual-prompt:visual-prompt '
        "'/home/u/novel.txt' --series 'x'\\n</USER_REQUEST>\"}\n"
    )

    def _armed_artifact(self, root: Path, transcript_body: str) -> Path:
        artifact = root / 'artifact'
        artifact.mkdir()
        (artifact / 'transcript.jsonl').write_text(transcript_body, encoding='utf-8')
        return artifact

    def test_user_invocation_line_arms_guard_without_a_contract_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = self._armed_artifact(Path(tmp), self.USER_TURN)
            payload = {**base_payload('primary', artifact), 'toolCall': {
                'name': 'invoke_subagent', 'args': {},
            }}
            result = run_guard('pre-tool-use', payload, {})
        self.assertEqual('deny', result['decision'])
        self.assertIn('delegation', result['reason'])

    def _recorded_state(self, transcript_body: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = self._armed_artifact(Path(tmp), transcript_body)
            run_guard('pre-invocation', base_payload('primary', artifact), {})
            return json.loads(
                (artifact / '.visual-prompt-primary.json').read_text(encoding='utf-8'))

    def test_the_images_override_is_recorded_from_the_user_turn(self):
        pinned = self.USER_TURN.replace("--series 'x'", "--series 'x' --images 200")

        self.assertEqual(200, self._recorded_state(pinned)['images_override'])

    def test_a_count_the_model_types_later_is_not_an_override(self):
        # Only the user's own invocation line settles the number to be measured by.
        model_turn = '{"type":"MODEL_OUTPUT","content":"running with --images 40"}\n'

        state = self._recorded_state(self.USER_TURN + model_turn)

        self.assertIsNone(state['images_override'])

    def test_mentioning_the_command_mid_sentence_does_not_arm_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = self._armed_artifact(Path(tmp), (
                '{"type":"USER_INPUT","content":"<USER_REQUEST>\\n'
                'explain how /visual-prompt works\\n</USER_REQUEST>"}\n'
            ))
            payload = {**base_payload('unrelated', artifact), 'toolCall': {
                'name': 'invoke_subagent', 'args': {},
            }}
            result = run_guard('pre-tool-use', payload, {})
        self.assertEqual('allow', result['decision'])

    def test_first_armed_invocation_announces_rules_after_turn_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = self._armed_artifact(Path(tmp), self.USER_TURN)
            payload = {**base_payload('primary', artifact), 'invocationNum': 7}
            first = run_guard('pre-invocation', payload, {})
            second = run_guard('pre-invocation', payload, {})
        self.assertIn('GUARDED', first['injectSteps'][0]['ephemeralMessage'])
        self.assertIn('--require-authorship', first['injectSteps'][0]['ephemeralMessage'])
        self.assertEqual({}, second)

    def test_allowed_commands_are_forced_to_stay_synchronous(self):
        # Backgrounded helpers can only be read through manage_task, which this
        # guard forbids — on a slow mount that dead-ends the model on its own
        # output, so the guard pins WaitMsBeforeAsync instead.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = self._armed_artifact(root, self.USER_TURN)
            payload = {**base_payload('primary', artifact), 'toolCall': {
                'name': 'run_command', 'args': {
                    'CommandLine': f'python3 {ROOT}/scripts/load_input.py {root}/n.txt',
                    'Cwd': str(root), 'WaitMsBeforeAsync': 2000,
                }}}
            result = run_guard('pre-tool-use', payload, {'VP_GUARD_STATE': str(root / 'g.json')})
        self.assertEqual('allow', result['decision'])
        self.assertGreaterEqual(result['overwrite']['WaitMsBeforeAsync'], 60_000)

    def test_neutral_agy_tools_pass_while_unknown_capabilities_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = self._armed_artifact(root, self.USER_TURN)
            env = {'VP_GUARD_STATE': str(root / 'guard.json')}
            for tool, decision in (('notify_user', 'allow'), ('view_file_outline', 'allow'),
                                   ('mcp_tool', 'deny'), ('browser_subagent', 'deny')):
                with self.subTest(tool=tool):
                    payload = {**base_payload('primary', artifact), 'toolCall': {
                        'name': tool, 'args': {},
                    }}
                    self.assertEqual(decision, run_guard('pre-tool-use', payload, env)['decision'])


class StopGateTests(unittest.TestCase):
    """The run may not end on a failing legitimacy gate — but holds are bounded."""

    IMAGE_PROMPT = (
        '--- SCENE 001 ---\nCamera: close frame\nStory DNA: grounded beat\n'
        'Setting: quiet room\nComposition: layered depth\nSubject: lone traveler\n'
        'Action / Energy: opens a letter\nStyle: painted realism\n'
        'Lighting / Color: cool window light\nAtmosphere: restrained concern\n'
        'Negative: no logos, no text\n'
    )

    def _authored_run(self, root: Path) -> tuple[dict, dict[str, str]]:
        artifact = root / 'artifact'; work = root / '.work'
        artifact.mkdir(); work.mkdir()
        (work / 'scene-plan.md').write_text('| 1 | chapter | grounded beat |\n', encoding='utf-8')
        scene = work / 'scene-001.md'
        scene.write_text('scene body', encoding='utf-8')
        env = {'VP_GUARD_ACTIVE': '1', 'VP_GUARD_STATE': str(root / 'guard.json'),
               'VP_AUTHORSHIP_LOG': str(work / 'authorship.jsonl'),
               'VP_ALLOWED_WRITE_ROOTS': str(work)}
        payload = {**base_payload('primary', artifact), 'toolCall': {
            'name': 'write_to_file', 'args': {
                'TargetFile': str(scene), 'CodeContent': 'scene body',
            }}}
        run_guard('post-tool-use', payload, env)
        return base_payload('primary', artifact), env

    def _hold_until_release(self, payload: dict, env: dict[str, str], limit: int = 12) -> int:
        """Stop repeatedly without progress; return how many holds it took."""
        for attempt in range(1, limit + 1):
            if run_guard('stop', payload, env) == {}:
                return attempt
        self.fail(f'stop was still held after {limit} calls — unbounded')

    def test_stop_is_held_then_released_when_no_progress_follows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            # No assembled output yet -> the gate cannot pass.
            first = run_guard('stop', payload, env)
            self.assertEqual('continue', first['decision'])
            self.assertIn('assemble', first['reason'])
            self.assertLessEqual(self._hold_until_release(payload, env), 12)

    def test_passing_gates_are_held_until_the_merged_scene_files_are_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            (root / 'novel_image_prompts.txt').write_text(self.IMAGE_PROMPT, encoding='utf-8')
            held = run_guard('stop', payload, env)
            self.assertEqual('continue', held['decision'])
            self.assertIn('cleanup_work.py', held['reason'])
            # Doing the cleanup is what lets the run end.
            (root / '.work' / 'scene-001.md').unlink()
            self.assertEqual({}, run_guard('stop', payload, env))

    def test_template_stamped_output_holds_the_stop_even_with_valid_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            (root / 'novel_image_prompts.txt').write_text(
                ''.join(self.IMAGE_PROMPT.replace('SCENE 001', f'SCENE {n:03d}')
                        for n in (1, 2, 3)),
                encoding='utf-8',
            )
            held = run_guard('stop', payload, env)
        self.assertEqual('continue', held['decision'])
        self.assertIn('pair_copy', held['reason'])

    def test_yielded_turn_is_driven_on_while_scenes_are_still_missing(self):
        # Agy reports a model that stopped talking as TERMINATION_REASON_NO_TOOL_CALL,
        # not the lowercase label its embedded docs show.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            (root / '.work' / 'scene-plan.md').write_text(
                '| scene_id | chapter |\n|---|---|\n'
                + ''.join(f'| {n:03d} | 1 | beat |\n' for n in range(1, 6)),
                encoding='utf-8',
            )
            stop = {**payload, 'terminationReason': 'TERMINATION_REASON_NO_TOOL_CALL'}
            held = run_guard('stop', {**stop, 'executionNum': 1}, env)
            self.assertEqual('continue', held['decision'])
            self.assertIn('1/5 scenes', held['reason'])
            # Progress resets the stall budget, so a long run keeps going.
            for scene in range(2, 5):
                (root / '.work' / f'scene-{scene:03d}.md').write_text('body', encoding='utf-8')
                self.assertEqual('continue', run_guard(
                    'stop', {**stop, 'executionNum': scene}, env,
                )['decision'])

    def test_a_stalled_run_is_released_and_never_loops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            (root / '.work' / 'scene-plan.md').write_text(
                '| 001 | 1 | beat |\n| 002 | 1 | beat |\n', encoding='utf-8',
            )
            # The wire value carries no TERMINATION_REASON_ prefix; both spellings
            # and executionNum 0 (which is falsy) must behave the same.
            for reason in ('NO_TOOL_CALL', 'TERMINATION_REASON_NO_TOOL_CALL'):
                with self.subTest(reason=reason):
                    stop = {**payload, 'terminationReason': reason, 'executionNum': 0}
                    self.assertEqual('continue', run_guard('stop', stop, env)['decision'])
                    self._hold_until_release(stop, env)
                    (root / 'guard.stop').unlink(missing_ok=True)  # VP_GUARD_STATE sidecar

    def test_a_cleaned_run_may_end_and_is_not_asked_for_its_scenes_back(self):
        # cleanup_work.py removes scene-NNN.md once they are merged; the gate must
        # read completeness off the deliverable instead of demanding the files.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            work = root / '.work'
            (work / 'scene-plan.md').write_text(
                '| 001 | 1 | beat |\n| 002 | 1 | beat |\n', encoding='utf-8',
            )
            (root / 'novel_image_prompts.txt').write_text(
                self.IMAGE_PROMPT + self.IMAGE_PROMPT.replace('SCENE 001', 'SCENE 002')
                .replace('quiet room', 'storm-lit courtyard')
                .replace('opens a letter', 'draws a worn blade')
                .replace('cool window light', 'harsh lightning')
                .replace('restrained concern', 'braced defiance')
                .replace('close frame', 'wide low angle')
                .replace('grounded beat', 'the duel begins')
                .replace('layered depth', 'diagonal sweep')
                .replace('lone traveler', 'the old swordsman'),
                encoding='utf-8',
            )
            (work / 'scene-001.md').unlink()
            stop = {**payload, 'terminationReason': 'TERMINATION_REASON_NO_TOOL_CALL',
                    'executionNum': 1}
            self.assertEqual({}, run_guard('stop', stop, env))

    def test_error_and_non_model_stops_are_never_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            for extra in ({'error': 'interrupted'},
                          {'terminationReason': 'max_steps_exceeded'}):
                with self.subTest(stop=extra):
                    self.assertEqual({}, run_guard('stop', {**payload, **extra}, env))

    def test_plan_only_and_worker_sessions_opt_out_of_the_closing_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, env = self._authored_run(root)
            self.assertEqual({}, run_guard('stop', payload, {**env, 'VP_GUARD_STOP_GATE': '0'}))

    def test_a_scene_plan_alone_does_not_arm_the_closing_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / 'artifact'; work = root / '.work'
            artifact.mkdir(); work.mkdir()
            plan = work / 'scene-plan.md'
            plan.write_text('| 1 | chapter | grounded beat |\n', encoding='utf-8')
            env = {'VP_GUARD_ACTIVE': '1', 'VP_GUARD_STATE': str(root / 'guard.json'),
                   'VP_AUTHORSHIP_LOG': str(work / 'authorship.jsonl'),
                   'VP_ALLOWED_WRITE_ROOTS': str(work)}
            run_guard('post-tool-use', {**base_payload('primary', artifact), 'toolCall': {
                'name': 'write_to_file', 'args': {
                    'TargetFile': str(plan), 'CodeContent': 'plan',
                }}}, env)
            self.assertEqual({}, run_guard('stop', base_payload('primary', artifact), env))

    def test_unrelated_sessions_are_never_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / 'artifact'; artifact.mkdir()
            self.assertEqual({}, run_guard('stop', base_payload('other', artifact), {}))


if __name__ == '__main__':
    unittest.main()
