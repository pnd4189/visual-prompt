#!/usr/bin/env python3
"""Agy hook enforcing direct active-model authorship for visual-prompt."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows Agy has no fcntl; append-only records remain valid.
    fcntl = None

from active_model_policy import (
    FORBIDDEN_TOOLS, NEUTRAL_TOOLS, READ_TOOLS, SKILL_ROOT, WRITE_TOOLS,
    command_denial, state_path, target_path, write_denial,
)

# Measured on the wire: Agy sends the enum name with the TERMINATION_REASON_
# prefix stripped ("NO_TOOL_CALL"), not the lowercase label its embedded docs
# print. Compare on the suffix so either spelling works. Hold only the "model
# finished talking" endings — errors, cancels and budget limits must end at once.
HOLDABLE_STOPS = frozenset({'', 'UNSPECIFIED', 'NO_TOOL_CALL',
                            'TERMINAL_STEP_TYPE', 'MODEL_STOP'})
# Both counters advance on every hook call, and Agy fires each event twice, so
# these budgets are roughly double the number of real stops they allow.
MAX_STALLED_HOLDS = 3   # ~2 consecutive stops with no new scene, then release
MAX_TOTAL_HOLDS = 300   # ~150 stops; a 120-scene run needs about 40
SYNC_WAIT_MS = 600_000  # keep helper commands in the foreground even on gdrive

GUARD_MARKER = b'VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1'
# Agy records the raw user turn, not the expanded slash-command prompt, so the
# invocation line is the only arming signal that does not depend on the model
# choosing to read the contract first. Content is JSON-escaped in the
# transcript, hence the literal "\n" alternative.
INVOCATION_RE = re.compile(
    rb'<USER_REQUEST>(?:\\[rnt]|\s)*/(?:[A-Za-z0-9._-]+:)?visual-prompt\b'
)
HEAD_BYTES = 131_072
TAIL_BYTES = 262_144
# Mirrors SCENE_FILE_RE in check_run_legit.py — the closing gate and the guard
# must agree on what counts as an authored scene.
SCENE_FILE_RE = re.compile(r'^scene-\d{3}[a-zA-Z]?\.md$')
PLAN_ROW_RE = re.compile(r'^\s*\|\s*\d{1,3}[a-zA-Z]?\s*\|')
SCENE_BLOCK_RE = re.compile(r'^--- SCENE \d+[a-zA-Z]?(?: / \d+)? ---\s*$', re.MULTILINE)
GUARD_RULES = (
    'VISUAL-PROMPT GUARDED (Agy runtime). You are the primary active model: '
    'author every .work/scene-NNN.md yourself with the file-write tool using an '
    'absolute path, at most three scenes per write batch — then verify the files '
    'and continue straight into the next batch yourself, without stopping to ask. '
    'The scene count is already settled by calc_scene_count.py: never ask the user '
    'whether to shorten the run, sample a subset, or split it up, and never offer '
    'the batch driver as a way out — just run every planned scene. '
    'No subagent, background task, '
    'runtime generator script, or external model. Run only the canonical helpers '
    f'under {SKILL_ROOT}/scripts/ — one command per run_command call, no &&, ||, '
    'pipes, $(...) or backticks, and quote any path containing spaces. '
    'check_run_legit.py must be called with --require-authorship '
    '--authorship-log <work>/active-model-authorship.jsonl. The run cannot end '
    'while that gate fails. Never ask the user to run code on your behalf: if a '
    'gate fails, rewrite the flagged scenes — do not dress the output up to pass.'
)


def _transcript_armed(path: str | None) -> bool:
    """Arm on the user's /visual-prompt turn or on the contract marker."""
    if not path:
        return False
    try:
        with Path(path).open('rb') as stream:
            head = stream.read(HEAD_BYTES)
            stream.seek(0, os.SEEK_END)
            stream.seek(max(HEAD_BYTES, stream.tell() - TAIL_BYTES))
            window = head + stream.read()
    except OSError:
        return False
    return GUARD_MARKER in window or INVOCATION_RE.search(window) is not None


def _active(payload: dict) -> bool:
    if os.environ.get('VP_GUARD_ACTIVE') == '1' or _transcript_armed(payload.get('transcriptPath')):
        return True
    path = state_path(payload)
    if not path.exists():
        return False
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return True
    return (
        isinstance(state, dict)
        and state.get('schema') == 1
        and state.get('primary_conversation_id') == str(payload.get('conversationId') or '')
    )


def _claim_primary(payload: dict) -> tuple[dict, bool]:
    """Return the guard state and whether this call created (armed) it."""
    path = state_path(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        'schema': 1,
        'primary_conversation_id': str(payload.get('conversationId') or ''),
        'model': str(payload.get('modelName') or ''),
    }
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        loaded = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(loaded, dict) or loaded.get('schema') != 1:
            raise ValueError('invalid guard state')
        return loaded, False
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(state, stream, ensure_ascii=False)
        stream.write('\n')
    return state, True


def _log_path(target: Path) -> Path:
    configured = os.environ.get('VP_AUTHORSHIP_LOG')
    return Path(configured) if configured else target.parent / 'active-model-authorship.jsonl'


def _work_marker(payload: dict) -> Path:
    """Sidecar remembering which work dir this session authored scenes into."""
    return state_path(payload).with_suffix('.work')


def _stop_counter(payload: dict) -> Path:
    return state_path(payload).with_suffix('.stop')


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_provenance(target: Path) -> bool:
    log = _log_path(target)
    if not log.is_file():
        return False
    digest = _digest(target)
    try:
        records = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return any(
        record.get('schema') == 1
        and record.get('event') == 'creative_write'
        and record.get('conversation_id') == record.get('primary_conversation_id')
        and record.get('basename') == target.name
        and record.get('sha256') == digest
        for record in records if isinstance(record, dict)
    )


def _pre_invocation(payload: dict) -> dict:
    if not _active(payload):
        return {}
    state, claimed = _claim_primary(payload)
    if state.get('primary_conversation_id') != payload.get('conversationId'):
        message = 'Secondary agents cannot author visual-prompt artifacts.'
    elif claimed:
        # Arming can happen after invocation 0, and Agy calls each hook twice per
        # event, so the exclusive state claim is the one-shot announcement point.
        message = GUARD_RULES
    else:
        return {}
    return {'injectSteps': [{'ephemeralMessage': message}]}


def _pre_tool(payload: dict) -> dict:
    if not _active(payload):
        return {'decision': 'allow'}
    tool_call = payload.get('toolCall') or {}
    tool = tool_call.get('name')
    args = tool_call.get('args') or {}
    if tool in FORBIDDEN_TOOLS:
        return {'decision': 'deny', 'reason': FORBIDDEN_TOOLS[tool]}
    state, _ = _claim_primary(payload)
    if (state.get('primary_conversation_id') != payload.get('conversationId')
            and tool not in READ_TOOLS | NEUTRAL_TOOLS):
        reason = 'only the primary active-model conversation may mutate artifacts'
        return {'decision': 'deny', 'reason': reason}
    denial = None
    if tool in WRITE_TOOLS:
        denial = write_denial(args, payload)
        target = target_path(args)
        if (not denial and tool != 'write_to_file' and target is not None
                and target.name.startswith('scene-') and target.is_file()
                and not _has_provenance(target)):
            denial = 'unproven scene cannot be patched; rewrite its full content directly'
    elif tool == 'run_command':
        denial = command_denial(args, payload)
        if denial is None:
            # Agy backgrounds a command that outruns WaitMsBeforeAsync, and reading
            # a background task needs manage_task — which this guard forbids. On a
            # FUSE-backed run that dead-ends the model on its own helper output, so
            # keep guarded commands synchronous instead.
            return {'decision': 'allow', 'overwrite': {'WaitMsBeforeAsync': SYNC_WAIT_MS}}
    elif tool not in READ_TOOLS | NEUTRAL_TOOLS:
        denial = f'tool {tool!r} is outside the guarded visual-prompt capability set'
    return {'decision': 'deny', 'reason': denial} if denial else {'decision': 'allow'}


def _post_tool(payload: dict) -> dict:
    if not _active(payload) or payload.get('error'):
        return {}
    tool_call = payload.get('toolCall') or {}
    target = target_path(tool_call.get('args') or {})
    if (tool_call.get('name') not in WRITE_TOOLS or target is None
            or not target.is_file() or not target.name.startswith('scene-')):
        return {}
    state, _ = _claim_primary(payload)
    conversation = str(payload.get('conversationId') or '')
    if state.get('primary_conversation_id') != conversation:
        return {}
    record = {
        'schema': 1, 'event': 'creative_write', 'conversation_id': conversation,
        'primary_conversation_id': conversation, 'model': str(payload.get('modelName') or ''),
        'tool': tool_call.get('name'), 'target': str(target), 'basename': target.name,
        'sha256': _digest(target), 'size': target.stat().st_size,
    }
    log = _log_path(target)
    log.parent.mkdir(parents=True, exist_ok=True)
    if SCENE_FILE_RE.fullmatch(target.name):
        # Only numbered scenes mean "this session authored prompts"; scene-plan.md
        # alone must not arm the closing gate (plan-only sessions stop there).
        _work_marker(payload).write_text(f'{target.parent}\n{log}\n', encoding='utf-8')
    with log.open('a+', encoding='utf-8') as stream:
        if fcntl is not None:
            fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        for raw in stream:
            try:
                existing = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if all(existing.get(key) == record[key] for key in (
                'event', 'conversation_id', 'target', 'sha256',
            )):
                if fcntl is not None:
                    fcntl.flock(stream, fcntl.LOCK_UN)
                return {}
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        if fcntl is not None:
            fcntl.flock(stream, fcntl.LOCK_UN)
    return {}


def _gate_failure(work: Path, log: Path) -> str | None:
    """Run the closing canonical gates; return the first failure text, or None."""
    images = sorted(work.parent.glob('*_image_prompts.txt'))
    if not images:
        return ('no *_image_prompts.txt next to .work — assemble the final output '
                'with scripts/assemble_outputs.py before ending the run')
    helpers = SKILL_ROOT / 'scripts'
    gates = []
    # cleanup_work.py removes the scene files only after they are merged, and the
    # legitimacy gate rightly reads their absence as a skipped expander. Once the
    # deliverable itself accounts for every planned scene there is nothing left
    # for that gate to inspect, so drop it rather than weaken it.
    cleaned = (_scene_count(work) == 0
               and _assembled_scenes(work.parent) >= max(_planned_scenes(work), 1))
    if not cleaned:
        gates.append([sys.executable, str(helpers / 'check_run_legit.py'),
                      '--work', str(work), '--image', str(images[0]),
                      '--require-authorship', '--authorship-log', str(log)])
    # Anti-repetition is part of "done": template-stamped scenes must not be
    # shippable just because every file has valid provenance. This one reads the
    # deliverable, so it still applies after cleanup.
    gates.append([sys.executable, str(helpers / 'check_prompt_similarity.py'),
                  '--image', str(images[0])])
    for command in gates:
        try:
            # Both gates must finish inside the hook's own 120s budget.
            completed = subprocess.run(command, capture_output=True, text=True, timeout=45)
        except (OSError, subprocess.SubprocessError) as exc:
            return f'{Path(command[1]).name} could not run ({type(exc).__name__})'
        if completed.returncode != 0:
            return (completed.stdout + completed.stderr).strip()[:1500]
    return None


def _scene_count(work: Path) -> int:
    try:
        return sum(1 for entry in work.iterdir() if SCENE_FILE_RE.fullmatch(entry.name))
    except OSError:
        return 0


def _planned_scenes(work: Path) -> int:
    """How many scene rows the plan declares; 0 when there is no readable plan."""
    try:
        rows = (work / 'scene-plan.md').read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError):
        return 0
    return sum(1 for row in rows if PLAN_ROW_RE.match(row))


def _deliverable(folder: Path) -> Path | None:
    outputs = sorted(folder.glob('*_image_prompts.txt'))
    return outputs[0] if outputs else None


def _assembled_scenes(folder: Path) -> int:
    """Scene blocks already merged into the deliverable next to .work."""
    try:
        output = _deliverable(folder)
        return len(SCENE_BLOCK_RE.findall(output.read_text(encoding='utf-8'))) if output else 0
    except (OSError, UnicodeError):
        return 0


def _stop_reason(payload: dict) -> str:
    raw = str(payload.get('terminationReason') or '').strip().upper()
    prefix = 'TERMINATION_REASON_'
    return raw[len(prefix):] if raw.startswith(prefix) else raw


def _load_counter(payload: dict) -> dict:
    try:
        record = json.loads(_stop_counter(payload).read_text(encoding='utf-8'))
        return {'holds': int(record['holds']), 'scenes': int(record.get('scenes') or 0),
                'stalls': int(record.get('stalls') or 0)}
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return {'holds': 0, 'scenes': 0, 'stalls': 0}


def _stop(payload: dict) -> dict:
    """Drive a guarded run to completion instead of letting it pause or ship broken.

    Two reasons to refuse a stop: scenes are still missing (the model likes to
    write three and wait for a human), or the closing gates fail. Both are bounded
    by progress — two consecutive holds that produce no new scene end the run — so
    this can never become a loop.
    """
    if (not _active(payload) or payload.get('error')
            or os.environ.get('VP_GUARD_STOP_GATE') == '0'):
        return {}
    if _stop_reason(payload) not in HOLDABLE_STOPS:
        return {}
    marker = _work_marker(payload)
    if not marker.is_file():
        return {}
    state, _ = _claim_primary(payload)
    if state.get('primary_conversation_id') != str(payload.get('conversationId') or ''):
        return {}
    work_line, _, log_line = marker.read_text(encoding='utf-8').partition('\n')
    work = Path(work_line.strip())
    scenes, planned = _scene_count(work), _planned_scenes(work)
    # After cleanup_work.py the scene files are gone on purpose; the deliverable
    # itself then proves the run is complete, so do not demand them back.
    if planned and scenes < planned and _assembled_scenes(work.parent) < planned:
        message = (f'visual-prompt is only {scenes}/{planned} scenes in. Write the '
                   'next micro-batch now — do not stop to ask, do not summarise; '
                   'keep going until every scene file exists, then run the gates.')
    else:
        failure = _gate_failure(work, Path(log_line.strip()))
        if failure is None:
            if not scenes:
                return {}
            message = (f'the gates pass — now merge and tidy up: run '
                       f'{SKILL_ROOT}/scripts/cleanup_work.py --work "{work}" '
                       f'--image "{_deliverable(work.parent)}" to remove the '
                       f'{scenes} merged scene files, then report the summary.')
        else:
            message = ('visual-prompt run is not finished: the closing gate still '
                       f'fails. Fix the scenes yourself and re-run the gate.\n{failure}')
    # executionNum is not a reliable event key (it stays 0 for a whole print-mode
    # session), so every hook call moves the counters. Agy fires each event twice,
    # which just halves the effective budget — bounded either way, never a loop.
    record = _load_counter(payload)
    stalls = record['stalls'] + 1 if scenes <= record['scenes'] else 0
    if stalls > MAX_STALLED_HOLDS or record['holds'] >= MAX_TOTAL_HOLDS:
        return {}
    _stop_counter(payload).write_text(json.dumps({
        'holds': record['holds'] + 1, 'scenes': scenes, 'stalls': stalls,
    }), encoding='utf-8')
    return {'decision': 'continue', 'reason': message}


def main() -> int:
    event = sys.argv[1] if len(sys.argv) == 2 else ''
    payload = json.load(sys.stdin)
    guard_active = _active(payload)
    handlers = {'pre-invocation': _pre_invocation, 'pre-tool-use': _pre_tool,
                'post-tool-use': _post_tool, 'stop': _stop}
    try:
        result = handlers[event](payload) if event in handlers else {}
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        if event == 'pre-tool-use' and guard_active:
            result = {'decision': 'deny', 'reason': f'visual-prompt guard failed closed: {type(exc).__name__}'}
        else:
            result = {}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
