"""Argument-level policy for commands allowed by the Agy runtime guard."""
from __future__ import annotations

import hashlib
import os
import re
import shlex
from glob import glob, has_magic
from pathlib import Path

from active_model_policy import (
    FINAL_OUTPUT_RE, SKILL_ROOT, inside, lean_mode, remember_input_root, roots,
    state_path, write_denial,
)

# Helpers that receive the novel path the user named. The first one to resolve it
# teaches the guard which folder this run owns, so a direct /visual-prompt works
# from whatever workspace Agy happens to have open.
INPUT_HELPERS = {
    'load_input.py': None,                 # positional
    'check_previous_continuity.py': None,  # positional
    'assemble_qa.py': '--input',
    'assemble_outputs.py': '--input',
    'calc_scene_count.py': '--input',
}

ALLOWED_HELPERS = {
    'append_bible_row.py', 'assemble_outputs.py', 'assemble_qa.py',
    'calc_scene_count.py', 'check_anchor_consistency.py',
    'check_content_safety.py', 'check_previous_continuity.py',
    'check_prompt_similarity.py', 'check_run_legit.py', 'cleanup_work.py',
    'load_input.py',
    'validate_artifacts.py', 'validate_scene_plan.py', 'worker_manifest.py',
}
PROMPT_OUTPUT_RE = re.compile(r'_(?:image|video)_prompts\.txt$')
SKILL_ROOT_TOKEN = '__VP_SKILL_ROOT__'
SCENE_FILE_RE = re.compile(r'^scene-\d{3}[a-zA-Z]?\.md$')
MAX_BULK_SCENE_DELETES = 10  # the repair loop touches a handful, not a run


def _is_canonical_helper(script: Path) -> bool:
    """Accept a helper from any install prefix, by name and byte identity.

    setup.bat copies the whole skill when Windows denies symlinks, and Agy keeps
    its own plugin copy, so pinning the allowlist to one prefix would deny every
    legitimate helper there. Content identity keeps the allowlist strict: an
    edited or invented script never matches its canonical bytes.
    """
    if script.name not in ALLOWED_HELPERS:
        return False
    expected = (SKILL_ROOT / 'scripts' / script.name).resolve()
    if script == expected:
        return True
    try:
        return (
            script.parent.name == 'scripts'
            and hashlib.sha256(script.read_bytes()).digest()
            == hashlib.sha256(expected.read_bytes()).digest()
        )
    except OSError:
        return False


def _learn_input_root(name: str, tokens: list[str], cwd: Path, payload: dict) -> None:
    """Teach the guard the input folder, from an already-approved helper call."""
    if name not in INPUT_HELPERS:
        return
    option = INPUT_HELPERS[name]
    if option is None:
        candidates = [token for token in tokens if not token.startswith('-')]
        raw = candidates[0] if candidates else None
    else:
        raw = _one(tokens, option)
    if not raw:
        return
    target = _resolve(raw, cwd)
    if target.is_file():
        remember_input_root(payload, target.parent)


def _resolve(raw: str, cwd: Path) -> Path:
    path = Path(raw).expanduser()
    return (cwd / path).resolve() if not path.is_absolute() else path.resolve()


def _values(tokens: list[str], option: str) -> list[str]:
    values = []
    for index, token in enumerate(tokens):
        if token.startswith(option + '='):
            values.append(token.split('=', 1)[1])
        elif token == option and index + 1 < len(tokens):
            values.append(tokens[index + 1])
    return values


def _one(tokens: list[str], option: str) -> str | None:
    values = _values(tokens, option)
    return values[0] if len(values) == 1 and values[0] not in {'', '>'} else None


def _output_roots(payload: dict) -> list[Path]:
    configured = os.environ.get('VP_ALLOWED_OUTPUT_ROOTS')
    if not configured:
        return roots(payload)
    return [Path(raw).expanduser().resolve() for raw in configured.split(os.pathsep) if raw]


def _final_denial(target: Path, payload: dict, pattern=FINAL_OUTPUT_RE) -> str | None:
    target = target.resolve()
    if '.agents' in target.parts or inside(target, SKILL_ROOT):
        return 'canonical helpers cannot mutate guard-owned files'
    if not pattern.search(target.name):
        return 'canonical helper output does not match its owned artifact type'
    if not any(inside(target, root) for root in _output_roots(payload)):
        return 'canonical helper output is outside the guarded output roots'
    return None


LEAN_AWARE_HELPERS = {'assemble_outputs.py', 'validate_artifacts.py',
                      'check_prompt_similarity.py', 'check_run_legit.py',
                      'cleanup_work.py'}


def _lean_flag_denial(name: str, tokens: list[str], payload: dict) -> str | None:
    """The prompt spec is the user's choice, not the model's.

    Every lean-aware gate must run in the mode the user asked for. Left free, the
    model would simply pass --lean to whichever gate it wanted to satisfy cheaply.
    """
    if name not in LEAN_AWARE_HELPERS:
        return None
    wants_lean = lean_mode(payload)
    passed_lean = '--lean' in tokens
    if wants_lean and not passed_lean:
        return f'this run uses the lean prompt spec — {name} must be called with --lean'
    if passed_lean and not wants_lean:
        return (f'--lean was not requested for this run; {name} must validate the '
                'full deep spec')
    return None


def _helper_denial(name: str, tokens: list[str], cwd: Path, payload: dict) -> str | None:
    denial = _lean_flag_denial(name, tokens, payload)
    if denial:
        return denial
    path_options = {
        '--authorship-log', '--bible', '--history', '--input', '--output',
        '--report-json', '--work-dir',
    }
    if any(len(_values(tokens, option)) > 1 for option in path_options):
        return 'duplicate path options are forbidden for canonical helpers'
    if any(
        has_magic(value) or any(character in value for character in '{}')
        for option in path_options for value in _values(tokens, option)
    ):
        return 'path expansion is forbidden for canonical helper outputs'
    if name == 'append_bible_row.py':
        raw = _one(tokens, '--bible')
        if raw is None or _one(tokens, '--row') is None:
            return 'append_bible_row requires one bible target and one row'
        target = _resolve(raw, cwd)
        global_bibles = (Path.home() / '.gemini' / 'bibles').resolve()
        is_bible = target.name == 'character-bible.md' or (
            inside(target, global_bibles)
            and target.suffix.casefold() == '.md'
            and not target.name.endswith('-visual-history.md')
        )
        return write_denial({'TargetFile': str(target)}, payload) if is_bible else (
            'append_bible_row may only update a character bible'
        )

    if name in {'assemble_outputs.py', 'assemble_qa.py'}:
        raw_input = _one(tokens, '--input')
        if raw_input is None:
            return f'{name} requires exactly one --input path'
        input_path = _resolve(raw_input, cwd)
        suffix = '_image_prompts.txt' if name == 'assemble_outputs.py' else '_qa.txt'
        denial = _final_denial(input_path.parent / f'{input_path.stem}{suffix}', payload)
        if denial or name == 'assemble_outputs.py':
            return denial
        raw_work = _one(tokens, '--work-dir')
        work = _resolve(raw_work, cwd) if raw_work else input_path.parent / '.work'
        return write_denial({'TargetFile': str(work / 'chapters_qa.json')}, payload,
                            from_helper=True)

    if name in {'check_anchor_consistency.py', 'check_content_safety.py'} \
            and '--fix' in tokens:
        raw = _one(tokens, '--output')
        return _final_denial(_resolve(raw, cwd), payload, PROMPT_OUTPUT_RE) if raw else (
            f'{name} --fix requires exactly one --output path'
        )

    if name == 'check_prompt_similarity.py':
        forbidden = {'--soft', '--near', '--max-pair-copies', '--max-exact-per-field'}
        if any(token.split('=', 1)[0] in forbidden for token in tokens):
            return 'similarity thresholds are immutable in guarded mode'
        if '--extract-history' in tokens:
            raw = _one(tokens, '--history')
            target = _resolve(raw, cwd) if raw else None
            global_bibles = (Path.home() / '.gemini' / 'bibles').resolve()
            if target is None or not inside(target, global_bibles) \
                    or not target.name.endswith('-visual-history.md'):
                return 'history extraction may only update the series visual history'

    if name == 'cleanup_work.py':
        raw_work, raw_image = _one(tokens, '--work'), _one(tokens, '--image')
        if raw_work is None or raw_image is None:
            return 'cleanup_work requires exactly one --work and one --image path'
        work = _resolve(raw_work, cwd)
        if work.name != '.work':
            return 'cleanup_work may only clean a .work directory'
        denial = write_denial({'TargetFile': str(work / 'scene-001.md')}, payload)
        return denial or _final_denial(_resolve(raw_image, cwd), payload, PROMPT_OUTPUT_RE)

    if name == 'check_run_legit.py':
        if '--purge-skill-dir' in tokens:
            return 'the active model cannot purge or mutate the skill directory'
        if '--require-authorship' not in tokens or _one(tokens, '--authorship-log') is None:
            return 'Agy legitimacy checks must require active-model authorship provenance'
        report = _one(tokens, '--report-json')
        if report:
            target = _resolve(report, cwd)
            if target.suffix.casefold() != '.json':
                return 'legitimacy reports must be JSON artifacts'
            return write_denial({'TargetFile': str(target)}, payload)
    return None


def command_denial(args: dict, payload: dict) -> str | None:
    command = args.get('CommandLine')
    if not isinstance(command, str) or not command.strip():
        return 'empty command is not allowed'
    if '\n' in command or '$' in command or '`' in command:
        return 'runtime generator shell composition is forbidden'
    try:
        # The skill root may contain spaces, and an unquoted absolute helper path
        # would then split into fragments and look like a rogue script. Mask the
        # literal root before lexing and restore it afterwards, so the allowlist
        # sees the real path either way. Masking grants nothing: the placeholder
        # only ever expands back to the same root the model already typed.
        lexer = shlex.shlex(
            command.replace(str(SKILL_ROOT), SKILL_ROOT_TOKEN),
            posix=True, punctuation_chars=';&|<>',
        )
        lexer.whitespace_split = True
        tokens = [token.replace(SKILL_ROOT_TOKEN, str(SKILL_ROOT)) for token in lexer]
    except ValueError:
        return 'unparseable shell command is forbidden'
    if not tokens:
        return 'empty command is not allowed'
    if any(
        token != '>' and token and all(character in ';&|<>' for character in token)
        for token in tokens
    ):
        return 'runtime generator shell composition is forbidden'
    if any('>' in token and token != '>' for token in tokens) or tokens.count('>') > 1:
        return 'unsafe output redirection is forbidden'
    cwd = Path(args.get('Cwd') or '.').expanduser().resolve()
    if tokens[0] in {'python', 'python3'}:
        if len(tokens) < 2 or tokens[1] in {'-', '-c', '-m'}:
            return 'runtime generator Python modes are forbidden'
        script = _resolve(tokens[1], cwd)
        if not _is_canonical_helper(script):
            return ('only canonical deterministic helper scripts may run; quote any '
                    f'path containing spaces and call them under {SKILL_ROOT}/scripts/')
        if '>' in tokens:
            index = tokens.index('>')
            if index + 1 >= len(tokens):
                return 'invalid output redirection'
            denial = write_denial({'TargetFile': str(_resolve(tokens[index + 1], cwd))},
                                  payload, from_helper=True)
            if denial:
                return denial
            tokens = tokens[:index]
        denial = _helper_denial(script.name, tokens[2:], cwd, payload)
        if denial is None:
            _learn_input_root(script.name, tokens[2:], cwd, payload)
        return denial
    if '>' in tokens:
        return 'only a canonical helper may redirect into a guarded artifact'
    if tokens[0] in {'sha1sum', 'sha256sum', 'wc', 'ls', 'stat', 'test'}:
        return None
    if tokens[0] not in {'mkdir', 'rm'}:
        return ('runtime generator or non-canonical command is forbidden; the shell '
                'may only run the canonical python3 helpers, sha1sum, sha256sum, wc, '
                'ls, stat, test, mkdir -p, rm -f — read files with view_file instead')
    expected_flag = '-p' if tokens[0] == 'mkdir' else '-f'
    if len(tokens) < 3 or tokens[1] != expected_flag:
        return f'only scoped {tokens[0]} {expected_flag} is allowed'
    allowed_roots = roots(payload)
    scene_targets = 0
    for raw in tokens[2:]:
        if any(character in raw for character in '{}[]'):
            return 'brace and character-class expansion is forbidden for mutations'
        candidates = glob(str(_resolve(raw, cwd))) if has_magic(raw) else [str(_resolve(raw, cwd))]
        scene_targets += sum(1 for c in candidates if SCENE_FILE_RE.fullmatch(Path(c).name))
        for candidate in candidates:
            target = Path(candidate).resolve()
            if not any(inside(target, root) for root in allowed_roots):
                return 'filesystem mutation is outside the guarded work root'
            if not os.environ.get('VP_ALLOWED_WRITE_ROOTS') and '.work' not in target.parts:
                return 'direct visual-prompt filesystem mutation is limited to .work'
            protected_paths = {state_path(payload).expanduser().resolve()}
            if os.environ.get('VP_AUTHORSHIP_LOG'):
                protected_paths.add(Path(os.environ['VP_AUTHORSHIP_LOG']).expanduser().resolve())
            if target.name == 'active-model-authorship.jsonl' or target in protected_paths \
                    or '.agents' in target.parts or inside(target, SKILL_ROOT):
                return 'guard state, provenance, and policy files are immutable'
            denial = write_denial({'TargetFile': str(target / 'placeholder.md')}, payload)
            if denial:
                return denial
    # Deleting a few flagged scenes to regenerate them is the repair loop. Wiping
    # them wholesale once the output exists is the post-run tidy-up, and that must
    # go through cleanup_work.py — which refuses while the similarity gate fails.
    # Skipping it is how a run once destroyed the only means of fixing itself.
    if scene_targets > MAX_BULK_SCENE_DELETES and _assembled_output_exists(payload, cwd):
        return (f'refusing to delete {scene_targets} scene files by hand — rewrite '
                'flagged scenes individually, or run cleanup_work.py once the gates '
                'pass; it verifies the output before removing the originals')
    return None


def _assembled_output_exists(payload: dict, cwd: Path) -> bool:
    for root in [*roots(payload), cwd]:
        try:
            if any(root.glob('*_image_prompts.txt')):
                return True
        except OSError:
            continue
    return False
