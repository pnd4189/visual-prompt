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
    'manage_task': ('background execution is forbidden during visual-prompt '
                    'generation; if a command was backgrounded anyway, read its '
                    'output with view_file on the task log under '
                    '<artifactDirectoryPath>/.system_generated/tasks/, then carry on'),
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
SCENE_FILE_RE = re.compile(r'^scene-\d{3}[a-zA-Z]?\.md$')
QA_CHAPTER_FILE_RE = re.compile(r'^qa-chapter-(\d+)\.md$')
LEAN_IMAGE_FIELDS = ('Subject', 'Setting', 'Action', 'Style', 'Negative')
# The lean contract gives Setting and Action an 8-20 word range. Enforced here so
# a stub is refused as it is written: validate_artifacts checks the same range,
# but only when the model runs it, and three runs in a row did not run it per
# batch. The ceiling sits far above the 18-word Vietnamese prose a healthy run
# produced — assemble_outputs holds the whole lean body to 60-220 words, so this
# only has to catch one field eating the prompt.
LEAN_FIELD_MIN_WORDS = 8
LEAN_FIELD_MAX_WORDS = 40
LEAN_MEASURED_FIELDS = ('Setting', 'Action')
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


def _guard_state(payload: dict) -> dict:
    try:
        state = json.loads(state_path(payload).read_text(encoding='utf-8'))
        return state if isinstance(state, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        return {}


def lean_mode(payload: dict) -> bool:
    """Whether the user asked for the lean prompt spec, per the guard state.

    The mode has to come from the invocation the user typed, not from the flags
    the model chooses: given the choice, the model takes the cheaper standard.
    The guard records it when it claims the session, in a file it owns.
    """
    return bool(_guard_state(payload).get('lean'))


def worker_mode(payload: dict) -> bool:
    """A Pass-2 worker starts at scene expansion, off a frozen snapshot."""
    return bool(_guard_state(payload).get('worker'))


def images_override(payload: dict) -> int | None:
    """The image total the user pinned with --images, or None for the auto count."""
    value = _guard_state(payload).get('images_override')
    return value if isinstance(value, int) else None


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


def _loaded_chapter_ids(source: Path) -> set[int]:
    """Chapter ids load_input.py put in chapters.json; empty when unreadable."""
    try:
        rows = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return set()
    if not isinstance(rows, list):
        return set()
    return {int(row['id']) for row in rows
            if isinstance(row, dict) and str(row.get('id', '')).isdigit()}


def write_denial(args: dict, payload: dict, from_helper: bool = False,
                 tool: str | None = None) -> str | None:
    """Vet a write target. `from_helper` marks a canonical helper's own output.

    `tool` names the write tool, so a whole-file write can be held to a shape a
    partial edit cannot be judged on.
    """
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
    # A scene file the artifact gate can bind to its plan row: frontmatter, then a
    # "## Image Prompt" heading, then — in lean mode — five labelled fields. Runs
    # have shipped both halves broken (2026-08-10: heading with prose and no
    # fields; 2026-08-11: fields with no heading at all, 300 of them), and each
    # time the gate only objected at the end and every scene had to be rewritten.
    # Judge a whole-file write only: a partial edit carries a fragment, so holding
    # it to the full shape would block the repair itself.
    if tool == 'write_to_file' and SCENE_FILE_RE.fullmatch(target.name):
        body = '\n'.join(_strings(args))
        if '## Image Prompt' not in body:
            return ('a scene file needs its frontmatter (scene_id, cache_key, '
                    'source_anchor, has_video) followed by a "## Image Prompt" '
                    'heading — without them the artifact gate cannot bind the scene '
                    'to its plan row, and every scene has to be rewritten at the end')
        if lean_mode(payload):
            absent = [f for f in LEAN_IMAGE_FIELDS
                      if not re.search(rf'^{f}:', body, re.MULTILINE)]
            if absent:
                return ('this run uses the lean prompt spec: every scene needs the '
                        f'labelled fields {LEAN_IMAGE_FIELDS}, and this one is missing '
                        f'{absent}. Write them as separate "Field: value" lines, not as '
                        'one paragraph — the repetition gate compares those fields and '
                        'cannot read prose')
            for field in LEAN_MEASURED_FIELDS:
                match = re.search(rf'^{field}:[ \t]*(.+)$', body, re.MULTILINE)
                words = len(match.group(1).split()) if match else 0
                if not LEAN_FIELD_MIN_WORDS <= words <= LEAN_FIELD_MAX_WORDS:
                    return (f'lean {field} has {words} word(s); the spec asks for '
                            f'{LEAN_FIELD_MIN_WORDS}-20. A stub like "living room" '
                            'tells the image model nothing and forces scenes to '
                            'repeat — describe this moment\'s place and action')
    # The scene plan is the first creative artifact, and every row of it cites the
    # QA'd chapter text. Writing it before that text exists means the whole plan is
    # ungrounded — observed 2026-08-10, a run that jumped here from genre detection
    # and wrote 100 scenes no gate could check. The stop gate catches this too, but
    # only after the scenes are written; refuse at the point the shortcut is taken.
    # Same reasoning one step earlier. A proofread is a rewrite OF something: with
    # no chapters.json there is nothing to rewrite, and the model wrote nine
    # chapters of a different novel from memory before anything objected — the
    # assembler catches it now, but only after the whole QA pass is spent
    # (observed 2026-08-13).
    qa_match = QA_CHAPTER_FILE_RE.fullmatch(target.name)
    if qa_match:
        source = target.parent / 'chapters.json'
        if not source.exists():
            return ('qa-chapter files cannot be written before .work/chapters.json '
                    'exists — it is the loaded text this pass is supposed to be '
                    'proofreading. Run STEP 1 (load_input.py) on the input file '
                    'first; proofreading from memory produces chapters that were '
                    'never in the novel')
        # Loading the right file is not the same as proofreading it. Twice in one
        # afternoon a run loaded chapters 17-20 and then wrote chapters 321-330 of
        # a different novel from memory, once with the correct source sitting in
        # .work the whole time (observed 2026-08-13). The id is the cheapest place
        # to notice, and the first file is the cheapest moment.
        loaded = _loaded_chapter_ids(source)
        chapter_id = int(qa_match.group(1))
        if loaded and chapter_id not in loaded:
            return (f'chapter {chapter_id} is not in .work/chapters.json, which holds '
                    f'{sorted(loaded)[:6]}. Proofread the chapters that were loaded '
                    f'from the input file — a chapter that was never loaded is one '
                    f'you are writing from memory, not proofreading')
    if target.name == 'scene-plan.md' and not (target.parent / 'chapters_qa.json').exists():
        return ('scene-plan.md cannot be written before .work/chapters_qa.json '
                'exists — it is the text every source_anchor is checked against. '
                'Run STEP 1 (load_input.py) and STEP 1.5 (the QA loop) first, even '
                'when the input file is already named *_qa.txt')
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

    # The gate says HALT; the model keeps going. validate_scene_plan writes
    # plan.hash only when the plan is clean, so its absence means every row a
    # scene would expand was rejected — 77 scenes were written this way on a plan
    # carrying 26 invented anchors and 42 invented characters (2026-08-11). The
    # stop gate already refuses to end such a run, but only after the hour is
    # spent. Refuse the first scene instead. A worker legitimately starts here,
    # off a frozen snapshot that keeps its plan elsewhere.
    if (SCENE_FILE_RE.fullmatch(target.name) and not worker_mode(payload)
            and not (target.parent / 'plan.hash').is_file()):
        return ('the plan gate has not passed: .work/plan.hash does not exist. '
                'validate_scene_plan.py writes it only on a clean plan, so scenes '
                'written now would expand rows the gate rejected. Fix the flagged '
                'rows, re-run the gate, and expand only once it exits 0')
    return None


def command_denial(args: dict, payload: dict) -> str | None:
    # Lazy import keeps path/write primitives in this module without a cycle.
    from active_model_command_policy import command_denial as check_command
    return check_command(args, payload)
