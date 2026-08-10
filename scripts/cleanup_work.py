#!/usr/bin/env python3
"""Delete the per-scene `.work/scene-NNN.md` files once the run is provably done.

Those files are intermediates: the deliverable is `<stem>_image_prompts.txt`.
They cannot be removed earlier, because the legitimacy and authorship gates read
them — so this helper refuses unless the assembled output already carries at
least as many scene blocks as the plan declares.

`scene-plan.md` and `active-model-authorship.jsonl` are kept: the plan is the
run's scene contract and the log is its authorship audit trail.

Exit 0 = cleaned (or nothing to clean), 2 = refused with a reason on stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCENE_FILE_RE = re.compile(r'^scene-\d{3}[a-zA-Z]?\.md$')
SCENE_BLOCK_RE = re.compile(r'^--- SCENE \d+[a-zA-Z]?(?: / \d+)? ---\s*$', re.MULTILINE)
PLAN_ROW_RE = re.compile(r'^\s*\|\s*\d{1,3}[a-zA-Z]?\s*\|', re.MULTILINE)


def _planned_scenes(work: Path) -> int:
    """Scene rows the plan declares; 0 when no readable plan remains."""
    try:
        return len(PLAN_ROW_RE.findall((work / 'scene-plan.md').read_text(encoding='utf-8')))
    except (OSError, UnicodeError):
        return 0


def _assembled_scenes(image: Path) -> int:
    try:
        return len(SCENE_BLOCK_RE.findall(image.read_text(encoding='utf-8')))
    except (OSError, UnicodeError):
        return 0


def _similarity_failure(image: Path) -> str | None:
    """The scene files are the only way to fix a repetitive output, so they may
    not be deleted until that output actually passes the anti-repetition gate."""
    command = [sys.executable, str(Path(__file__).resolve().parent / 'check_prompt_similarity.py'),
               '--image', str(image)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return f'similarity gate could not run ({type(exc).__name__})'
    return None if done.returncode == 0 else (done.stdout + done.stderr).strip()[:600]


def cleanup(work: Path, image: Path) -> tuple[int, dict]:
    if not work.is_dir():
        return 0, {'ok': True, 'removed': 0, 'reason': 'work dir already gone'}
    scenes = sorted(p for p in work.iterdir()
                    if p.is_file() and SCENE_FILE_RE.fullmatch(p.name))
    if not scenes:
        return 0, {'ok': True, 'removed': 0, 'reason': 'no scene files left'}
    if not image.is_file() or image.stat().st_size == 0:
        return 2, {'ok': False, 'reason': f'assembled output missing or empty: {image}'}
    planned, assembled = _planned_scenes(work), _assembled_scenes(image)
    if assembled == 0:
        return 2, {'ok': False, 'reason': f'no scene blocks found in {image.name}'}
    if planned and assembled < planned:
        return 2, {'ok': False, 'planned': planned, 'assembled': assembled,
                   'reason': 'assembled output has fewer scenes than the plan — '
                             'finish the run before cleaning up'}
    failure = _similarity_failure(image)
    if failure is not None:
        return 2, {'ok': False, 'planned': planned, 'assembled': assembled,
                   'reason': 'similarity gate still fails — rewrite the flagged '
                             'scenes and re-assemble before cleaning up',
                   'similarity': failure}
    for scene in scenes:
        scene.unlink()
    return 0, {'ok': True, 'removed': len(scenes), 'planned': planned,
               'assembled': assembled, 'kept': ['scene-plan.md',
                                                'active-model-authorship.jsonl']}


def main() -> int:
    parser = argparse.ArgumentParser(description='Remove merged per-scene files')
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path,
                        help='assembled <stem>_image_prompts.txt')
    args = parser.parse_args()
    code, report = cleanup(args.work.expanduser(), args.image.expanduser())
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
