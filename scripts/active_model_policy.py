"""Capability policy shared by the visual-prompt Agy runtime hook."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
WRITE_TOOLS = {'write_to_file', 'replace_file_content', 'multi_replace_file_content'}
READ_TOOLS = {
    'view_file', 'view_file_outline', 'view_code_item', 'view_content_chunk',
    'list_dir', 'list_directory', 'find', 'find_by_name', 'grep_search',
    'code_search', 'read_terminal', 'command_status',
}
# Agy step types that neither read artifacts nor author content. Everything
# outside READ_TOOLS | NEUTRAL_TOOLS | WRITE_TOOLS | {'run_command'} stays
# denied, so an unknown capability can never become a silent bypass.
NEUTRAL_TOOLS = {
    'ask_question', 'notify_user', 'suggested_responses', 'memory',
    'retrieve_memory', 'brain_update', 'checkpoint', 'task_boundary',
    'code_acknowledgement', 'finish',
}
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
# Scratch artifacts that a canonical helper owns. Hand-writing chapters_qa.json
# skips assemble_qa.py, which is also what emits <stem>_qa.txt — the run then
# looks finished to the model and fails the driver's output check, costing a full
# retry. Deny the shortcut instead of paying for it.
HELPER_OWNED_SCRATCH = {'chapters.json', 'chapters_qa.json'}
SOURCE_CODE_RE = re.compile(
    r'^[ \t]*(?:import\s+[A-Za-z_][\w.]*'
    r'|from\s+[A-Za-z_][\w.]*\s+import\s'
    r'|def\s+\w+\s*\('
    r'|with\s+open\s*\('
    r'|subprocess\.(?:run|Popen|call)\s*\()',
    re.MULTILINE,
)


def state_path(payload: dict) -> Path:
    configured = os.environ.get('VP_GUARD_STATE')
    base = Path(payload.get('artifactDirectoryPath') or '.')
    return Path(configured) if configured else base / '.visual-prompt-primary.json'


def _input_root_marker(payload: dict) -> Path:
    return state_path(payload).with_suffix('.root')


def remember_input_root(payload: dict, folder: Path) -> None:
    """Record the novel folder this session processes — once, never re-pointed.

    A direct `/visual-prompt <path>` is normally invoked from whatever workspace
    Agy happens to have open, so the run's own `.work/` would fall outside the
    launch directory and every write would be denied. The folder of the input the
    user named is the authoritative scope; it is learned from the first canonical
    helper that resolves that input, and the exclusive create means a later call
    cannot widen the scope somewhere else.
    """
    marker = _input_root_marker(payload)
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        return
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        stream.write(f'{folder}\n')


def input_root(payload: dict) -> Path | None:
    try:
        recorded = _input_root_marker(payload).read_text(encoding='utf-8').strip()
    except (OSError, UnicodeError):
        return None
    return Path(recorded) if recorded else None


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
        learned = input_root(payload)
        if learned is not None:
            raw.append(str(learned))
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


def write_denial(args: dict, payload: dict, from_helper: bool = False) -> str | None:
    """Vet a write target. `from_helper` marks a canonical helper's own output."""
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
        # Terse refusals made the model retry variants for minutes (observed
        # 2026-08-10). Close the door explicitly and point at the only way through.
        return ('runtime code creation is forbidden and no variant of it will pass — '
                'this skill has no generator path. Write .work/scene-plan.md and each '
                '.work/scene-NNN.md yourself with the file-write tool, three scenes '
                'per batch, and keep going until the plan is fully expanded')
    if any(value.lstrip().startswith('#!') for value in _strings(args)):
        return 'runtime code shebangs are forbidden'
    # A model blocked from writing .py will write the same program into a .md and
    # ask a human to run it (observed 2026-08-09: .work/fix.md, a script that
    # stamped scene ids into duplicate fields to fake its way past the similarity
    # gate). Scene prose never opens files or imports modules.
    if any(SOURCE_CODE_RE.search(value) for value in _strings(args)):
        return 'runtime code disguised as a text artifact is forbidden'
    if target.suffix.casefold() not in CONTENT_SUFFIXES:
        return 'only direct text artifacts are writable in guarded mode'
    if FINAL_OUTPUT_RE.search(target.name):
        return 'final outputs must be created by the canonical assembler'
    if not from_helper and target.name in HELPER_OWNED_SCRATCH:
        return (f'{target.name} is produced by a canonical helper '
                '(load_input.py / assemble_qa.py) — run it instead of writing the file')
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
        roots_hint = os.pathsep.join(str(root) for root in allowed_roots)
        return f'write target is outside the guarded artifact roots ({roots_hint})'
    return None


def command_denial(args: dict, payload: dict) -> str | None:
    # Lazy import keeps path/write primitives in this module without a cycle.
    from active_model_command_policy import command_denial as check_command
    return check_command(args, payload)
