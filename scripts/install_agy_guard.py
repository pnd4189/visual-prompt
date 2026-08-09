#!/usr/bin/env python3
"""Install the visual-prompt runtime guard without replacing other Agy hooks."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

HOOK_NAME = 'visual-prompt-active-model-guard'
LAUNCHER_NAME = 'visual-prompt-active-model-guard.py'


def _launcher_text(guard_script: Path) -> str:
    return (
        '"""Launch the installed visual-prompt guard from its source bundle."""\n'
        'import runpy\n'
        'import sys\n'
        'from pathlib import Path\n\n'
        f'GUARD_SCRIPT = Path({str(guard_script)!r})\n'
        'sys.path.insert(0, str(GUARD_SCRIPT.parent))\n'
        "runpy.run_path(str(GUARD_SCRIPT), run_name='__main__')\n"
    )


def _guard_config(repo_root: Path, launcher: Path) -> tuple[dict, str]:
    source = repo_root / 'hooks.json'
    guard_script = (repo_root / 'scripts' / 'active_model_guard.py').resolve()
    payload = json.loads(source.read_text(encoding='utf-8'))
    guard = payload.get(HOOK_NAME)
    if not isinstance(guard, dict) or not guard_script.is_file():
        raise ValueError('visual-prompt guard bundle is incomplete')
    if any(character.isspace() for character in str(launcher)):
        raise ValueError('Agy hook launcher path cannot contain whitespace')
    python_command = 'python' if os.name == 'nt' else 'python3'
    for phase in guard.values():
        if not isinstance(phase, list):
            continue
        for entry in phase:
            hooks = entry.get('hooks', [entry]) if isinstance(entry, dict) else []
            for hook in hooks:
                command = hook.get('command', '') if isinstance(hook, dict) else ''
                event = command.rsplit(' ', 1)[-1]
                if event not in {'pre-invocation', 'pre-tool-use', 'post-tool-use'}:
                    raise ValueError(f'unexpected guard command: {command}')
                hook['command'] = f'{python_command} {launcher} {event}'
    return guard, _launcher_text(guard_script)


def _atomic_write(path: Path, rendered: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f'.{path.name}.', dir=path.parent, text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(rendered)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def install(repo_root: Path, target: Path) -> bool:
    if target.exists() or target.is_symlink():
        current_text = target.read_text(encoding='utf-8')
        current = json.loads(current_text)
        if not isinstance(current, dict):
            raise ValueError('existing Agy hooks config must be a JSON object')
    else:
        current_text = ''
        current = {}
    launcher = Path(os.path.abspath(target.parent / LAUNCHER_NAME))
    guard, launcher_text = _guard_config(repo_root.resolve(), launcher)
    current[HOOK_NAME] = guard
    rendered = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
    launcher_current = (
        launcher.read_text(encoding='utf-8')
        if launcher.is_file() and not launcher.is_symlink() else ''
    )
    changed = launcher_current != launcher_text or current_text != rendered
    if launcher_current != launcher_text:
        _atomic_write(launcher, launcher_text)
    if current_text != rendered:
        _atomic_write(target, rendered)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    args = parser.parse_args()
    try:
        changed = install(args.repo_root, args.target.expanduser())
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f'ERROR: cannot install Agy runtime guard: {exc}', file=sys.stderr)
        return 2
    status = 'installed' if changed else 'already current'
    print(f'[OK] Agy runtime guard {status}: {args.target.expanduser()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
