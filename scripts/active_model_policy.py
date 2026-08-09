"""Capability policy shared by the visual-prompt Agy runtime hook."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
WRITE_TOOLS = {'write_to_file', 'replace_file_content', 'multi_replace_file_content'}
READ_TOOLS = {'view_file', 'list_dir', 'find_by_name', 'grep_search'}
FORBIDDEN_TOOLS = {
    'invoke_subagent': 'delegation is forbidden: the active model must author every scene',
    'define_subagent': 'delegation is forbidden: the active model must author every scene',
    'send_message': 'delegation is forbidden: the active model must author every scene',
    'manage_subagents': 'delegation is forbidden: the active model must author every scene',
    'manage_task': 'background execution is forbidden during visual-prompt generation',
    'schedule': 'background execution is forbidden during visual-prompt generation',
}
CODE_SUFFIXES = {
    '.py', '.pyw', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.sh', '.bash',
    '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.rb', '.pl', '.php', '.lua',
    '.r', '.ipynb', '.go', '.rs', '.java', '.cs', '.c', '.cc', '.cpp',
}
CONTENT_SUFFIXES = {'.md', '.json', '.txt', '.hash'}
FINAL_OUTPUT_RE = re.compile(r'_(?:image|video|music)_prompts\.txt$|_qa\.txt$')


def state_path(payload: dict) -> Path:
    configured = os.environ.get('VP_GUARD_STATE')
    base = Path(payload.get('artifactDirectoryPath') or '.')
    return Path(configured) if configured else base / '.visual-prompt-primary.json'


def _agy_launcher_cwd() -> Path | None:
    """Recover Agy's launch directory when CLI 1.1.x sends no workspace paths."""
    if os.name != 'posix' or not Path('/proc').is_dir():
        return None
    process_id = os.getppid()
    for _ in range(8):
        process = Path('/proc') / str(process_id)
        try:
            name = (process / 'comm').read_text(encoding='utf-8').strip()
            stat = (process / 'stat').read_text(encoding='utf-8')
            parent_id = int(stat[stat.rfind(')') + 2:].split()[1])
            if name in {'agy', 'agy.real'}:
                return Path(os.readlink(process / 'cwd')).resolve()
        except (OSError, ValueError, IndexError):
            return None
        if parent_id <= 1 or parent_id == process_id:
            return None
        process_id = parent_id
    return None


def roots(payload: dict) -> list[Path]:
    configured = os.environ.get('VP_ALLOWED_WRITE_ROOTS')
    if configured:
        raw = configured.split(os.pathsep)
    else:
        raw = list(payload.get('workspacePaths') or [])
        launcher_cwd = _agy_launcher_cwd()
        if launcher_cwd is not None:
            raw.append(str(launcher_cwd))
        else:
            raw.append(str(_hook_workspace_cwd()))
    resolved = [Path(item).expanduser().resolve() for item in raw if item]
    return list(dict.fromkeys(resolved))


def inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _hook_workspace_cwd() -> Path:
    hook_cwd = Path.cwd().resolve()
    return hook_cwd.parent if hook_cwd.name == '.agents' else hook_cwd


def target_path(args: dict) -> Path | None:
    raw = args.get('TargetFile')
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        return None
    return Path(raw).expanduser().resolve()


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings(nested)


def write_denial(args: dict, payload: dict) -> str | None:
    target = target_path(args)
    if target is None:
        return 'absolute TargetFile is required for guarded creative writes'
    if '.agents' in target.parts:
        return 'Agy hook configuration is guard-owned and read-only'
    protected = [state_path(payload)]
    configured_log = os.environ.get('VP_AUTHORSHIP_LOG')
    if configured_log:
        protected.append(Path(configured_log))
    if target.name == 'active-model-authorship.jsonl' or any(
        target == path.expanduser().resolve() for path in protected
    ):
        return 'guard state and authorship provenance are hook-owned and read-only'
    if inside(target, SKILL_ROOT):
        return 'the visual-prompt skill directory is read-only'
    if target.suffix.casefold() in CODE_SUFFIXES:
        return 'runtime code creation is forbidden; write the creative artifact directly'
    if any(value.lstrip().startswith('#!') for value in _strings(args)):
        return 'runtime code shebangs are forbidden'
    if target.suffix.casefold() not in CONTENT_SUFFIXES:
        return 'only direct text artifacts are writable in guarded mode'
    if FINAL_OUTPUT_RE.search(target.name):
        return 'final outputs must be created by the canonical assembler'
    allowed_roots = roots(payload)
    global_bibles = (Path.home() / '.gemini' / 'bibles').resolve()
    if inside(target, global_bibles) and target.name.endswith('-visual-history.md'):
        return 'visual history is writable only by the canonical history helper'
    if os.environ.get('VP_ALLOWED_WRITE_ROOTS'):
        in_scope = any(inside(target, root) for root in allowed_roots)
    else:
        in_scope = inside(target, global_bibles) or any(
            inside(target, root if root.name == '.work' else root / '.work')
            or (target.name == 'character-bible.md' and target.parent == root)
            for root in allowed_roots
        )
    if not in_scope:
        return 'write target is outside the guarded artifact roots'
    return None


def command_denial(args: dict, payload: dict) -> str | None:
    # Lazy import keeps path/write primitives in this module without a cycle.
    from active_model_command_policy import command_denial as check_command
    return check_command(args, payload)
