#!/usr/bin/env python3
"""Find the previous chapter file and extract excerpts for continuity QA."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from load_input import load_input  # type: ignore

EXCERPT_CHARS = 2200
MAX_CANDIDATES = 200


def _tail(text: str) -> str:
    return text.strip()[-EXCERPT_CHARS:]


def _head(text: str) -> str:
    return text.strip()[:EXCERPT_CHARS]


def _search_root(input_path: Path) -> Path:
    parent = input_path.parent
    return parent.parent if parent.parent != parent else parent


def _candidate_files(input_path: Path) -> list[Path]:
    root = _search_root(input_path)
    files: set[Path] = set()
    search_dirs = [input_path.parent, root]
    try:
        search_dirs.extend(p for p in root.iterdir() if p.is_dir())
    except OSError:
        pass

    for directory in search_dirs:
        try:
            paths = list(directory.glob('*.txt'))
        except OSError:
            continue
        for path in paths:
            try:
                if path.resolve() == input_path.resolve():
                    continue
            except OSError:
                continue
            if len(files) >= MAX_CANDIDATES:
                break
            if not path.is_file():
                continue
            files.add(path)
        if len(files) >= MAX_CANDIDATES:
            break

    filtered: list[Path] = []
    for path in files:
        name = path.name.lower()
        if name.endswith('_image_prompts.txt') or name.endswith('_video_prompts.txt'):
            continue
        filtered.append(path)
    return sorted(
        filtered,
        key=lambda p: (0 if p.name.lower().endswith('_qa.txt') else 1, str(p)),
    )


def _load_chapters(path: Path) -> list[dict]:
    try:
        return load_input(path)
    except Exception:
        return []


def find_previous(input_path: Path) -> dict:
    current = _load_chapters(input_path)
    if not current:
        return {
            'ok': False,
            'status': 'current_unreadable',
            'message': 'Cannot load current input.',
        }

    first = current[0]
    first_id = int(first.get('id', 0) or 0)
    if first_id <= 1:
        return {
            'ok': True,
            'status': 'first_chapter',
            'first_chapter': first_id,
            'message': 'Current file starts at chapter 1; no previous file is expected.',
        }

    expected_previous = first_id - 1
    inspected = 0

    def _search(paths) -> tuple[Path, dict] | None:
        nonlocal inspected
        for path in paths:
            try:
                if path.resolve() == input_path.resolve():
                    continue
            except OSError:
                continue
            chapters = _load_chapters(path)
            if not chapters:
                continue
            inspected += 1
            for chapter in reversed(chapters):
                if int(chapter.get('id', 0) or 0) == expected_previous:
                    return (path, chapter)
        return None

    # Fast path: search the input folder first. It holds only the current
    # batch's files (a handful), so this is a quick local glob — and for a
    # sequential batch the previous chapter file sits right here (file N-1 is
    # processed before file N). This avoids the broad scan below, which lists
    # every sibling subdir under the search root on the gdrive FUSE mount and
    # stalls in request_wait_answer (uninterruptible D state) for up to hours
    # on large folders — blocking the whole batch.
    fast = [p for p in input_path.parent.glob('*.txt')
            if not p.name.lower().endswith(('_image_prompts.txt', '_video_prompts.txt'))]
    fast.sort(key=lambda p: (0 if p.name.lower().endswith('_qa.txt') else 1, str(p)))
    best = _search(fast)
    # Fallback: broad scan across sibling dirs (e.g. a "ĐÃ QA" done-folder) only
    # if the previous chapter wasn't in the input folder. Bounded by run-folder's
    # `timeout` wrapper so a FUSE stall here can't block the batch.
    if not best:
        best = _search(_candidate_files(input_path))

    result = {
        'ok': best is not None,
        'status': 'candidate_found' if best else 'previous_not_found',
        'input_path': str(input_path),
        'first_chapter': first_id,
        'expected_previous_chapter': expected_previous,
        'current_first_title': first.get('title', ''),
        'current_first_excerpt': _head(first.get('text', '')),
        'search_root': str(_search_root(input_path)),
        'candidates_inspected': inspected,
    }
    if best:
        previous_path, previous_chapter = best
        result.update({
            'previous_path': str(previous_path),
            'previous_chapter': int(previous_chapter.get('id', 0) or 0),
            'previous_title': previous_chapter.get('title', ''),
            'previous_tail_excerpt': _tail(previous_chapter.get('text', '')),
        })
    else:
        # Batch-numbering fallback: when the current file parses a real chapter
        # id (>1) but every OTHER file in the SAME batch folder parses to id=1
        # (no `Chương N:` marker — the script's default fallback), the batch
        # filename numbering and the in-text chapter numbering don't match.
        # Treat the run as a fresh sequence so the batch doesn't HALT on a
        # numbering mismatch that's an artifact of the split, not a real
        # continuity gap. Only triggers when ALL batch siblings lack markers —
        # if any sibling has real markers, the original not-found stays.
        # Scope is the same batch folder (input_path.parent) on purpose: a
        # sibling "ĐÃ QA" folder can hold older files with real markers and
        # wrongly unlock this fallback even when THIS batch's numbering is
        # the inconsistent one.
        if first_id > 1:
            siblings = [p for p in input_path.parent.glob('*.txt')
                        if not p.name.lower().endswith(
                            ('_image_prompts.txt', '_video_prompts.txt', '_music_prompts.txt'))]
            real_marker_count = 0
            for p in siblings:
                try:
                    if p.resolve() == input_path.resolve():
                        continue
                except OSError:
                    continue
                chs = _load_chapters(p)
                if chs and any(int(c.get('id', 0) or 0) > 1 for c in chs):
                    real_marker_count += 1
                    break
            if real_marker_count == 0:
                result.update({
                    'status': 'first_chapter',
                    'message': (
                        f'Batch numbering appears inconsistent (this file id={first_id}, '
                        f'all other files in the same batch folder parse to id=1 — no '
                        f'`Chương N:` markers). Skipping continuity check; treating as '
                        f'start of sequence.'
                    ),
                })
                result['ok'] = True
        if not result['ok']:
            result['message'] = (
                f'No readable .txt candidate containing chapter {expected_previous} was found '
                f'under {_search_root(input_path)}.'
            )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Extract previous/current excerpts for continuity QA',
    )
    parser.add_argument('input', help='Current novel file')
    args = parser.parse_args()
    result = find_previous(Path(args.input))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('ok') else 2


if __name__ == '__main__':
    sys.exit(main())
