#!/usr/bin/env python3
"""Agy hook enforcing direct active-model authorship for visual-prompt."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows Agy has no fcntl; append-only records remain valid.
    fcntl = None

from active_model_policy import (
    FORBIDDEN_TOOLS, READ_TOOLS, WRITE_TOOLS, command_denial, state_path,
    target_path, write_denial,
)

GUARD_MARKER = 'VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1'


def _tail_contains(path: str | None) -> bool:
    if not path:
        return False
    try:
        with Path(path).open('rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 262_144))
            return GUARD_MARKER.encode() in stream.read()
    except OSError:
        return False


def _active(payload: dict) -> bool:
    if os.environ.get('VP_GUARD_ACTIVE') == '1' or _tail_contains(payload.get('transcriptPath')):
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


def _claim_primary(payload: dict) -> dict:
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
        return loaded
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(state, stream, ensure_ascii=False)
        stream.write('\n')
    return state


def _log_path(target: Path) -> Path:
    configured = os.environ.get('VP_AUTHORSHIP_LOG')
    return Path(configured) if configured else target.parent / 'active-model-authorship.jsonl'


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
    state = _claim_primary(payload)
    if state.get('primary_conversation_id') != payload.get('conversationId'):
        message = 'Secondary agents cannot author visual-prompt artifacts.'
    elif payload.get('invocationNum') == 0:
        message = ('VISUAL-PROMPT GUARDED: directly author every creative artifact; '
                   'never delegate or create/run a prompt generator. Maximum three scenes per turn.')
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
    state = _claim_primary(payload)
    if state.get('primary_conversation_id') != payload.get('conversationId') and tool not in READ_TOOLS:
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
    elif tool not in READ_TOOLS | {'ask_question'}:
        denial = 'tool is outside the guarded visual-prompt capability set'
    return {'decision': 'deny', 'reason': denial} if denial else {'decision': 'allow'}


def _post_tool(payload: dict) -> dict:
    if not _active(payload) or payload.get('error'):
        return {}
    tool_call = payload.get('toolCall') or {}
    target = target_path(tool_call.get('args') or {})
    if (tool_call.get('name') not in WRITE_TOOLS or target is None
            or not target.is_file() or not target.name.startswith('scene-')):
        return {}
    state = _claim_primary(payload)
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


def main() -> int:
    event = sys.argv[1] if len(sys.argv) == 2 else ''
    payload = json.load(sys.stdin)
    guard_active = _active(payload)
    handlers = {'pre-invocation': _pre_invocation, 'pre-tool-use': _pre_tool,
                'post-tool-use': _post_tool}
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
