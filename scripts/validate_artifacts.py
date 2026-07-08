#!/usr/bin/env python3
"""Validate visual-prompt intermediate and final artifacts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _io_utils import read_text_checked  # type: ignore

_ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')
_SCENE_FILE_RE = re.compile(r'^scene-(\d{3})\.md$')
_MUSIC_FILE_RE = re.compile(r'^music-(\d{3})\.md$')
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def _result(check: str, errors: list[str], **extra) -> dict:
    return {'ok': not errors, 'check': check, **extra, 'errors': errors}


def _read_nonempty(path: Path, errors: list[str], label: str) -> str | None:
    try:
        text = read_text_checked(path)
    except FileNotFoundError:
        errors.append(f'missing {label}: {path.name}')
        return None
    except (OSError, RuntimeError) as exc:
        errors.append(str(exc))
        return None
    if not text:
        errors.append(f'empty {label}: {path.name}')
        return None
    return text


def _frontmatter_fields(text: str) -> set[str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return set()
    return {
        line.split(':', 1)[0].strip()
        for line in match.group(1).splitlines()
        if ':' in line
    }


def parse_scene_plan(path: Path) -> tuple[list[int], set[int]]:
    scene_ids: list[int] = []
    video_ids: set[int] = set()
    for line in read_text_checked(path).splitlines():
        match = _ROW_RE.match(line)
        cells = [cell.strip() for cell in match.group(1).split('|')] if match else []
        if len(cells) < 6:
            continue
        raw_id = cells[0]
        if raw_id.lower() == 'scene_id' or set(raw_id) <= {'-', ':'}:
            continue
        if not re.match(r'^\d+$', raw_id):
            continue
        scene_id = int(raw_id)
        scene_ids.append(scene_id)
        if '\u2713' in cells[5]:
            video_ids.add(scene_id)
    return scene_ids, video_ids


def check_scenes(work_dir: Path, plan_path: Path) -> dict:
    errors: list[str] = []
    scene_ids, video_ids = parse_scene_plan(plan_path)
    expected = {f'scene-{scene_id:03d}.md' for scene_id in scene_ids}
    extra = {'expected': len(scene_ids), 'videos_expected': len(video_ids)}
    if not scene_ids:
        errors.append(f'no scene rows parsed from {plan_path}')

    for scene_id in scene_ids:
        path = work_dir / f'scene-{scene_id:03d}.md'
        text = _read_nonempty(path, errors, 'scene file')
        if text is None:
            return _result('scenes', errors, **extra)
        missing = {'scene_id', 'cache_key', 'has_video'} - _frontmatter_fields(text)
        if missing:
            errors.append(f'{path.name} missing frontmatter field(s): {sorted(missing)}')
        if '## Image Prompt' not in text:
            errors.append(f'{path.name} missing ## Image Prompt')
        if scene_id in video_ids and '## Video Prompt' not in text:
            errors.append(f'{path.name} missing ## Video Prompt')

    for path in work_dir.glob('scene-*.md'):
        if path.name == 'scene-plan.md':
            continue
        if not _SCENE_FILE_RE.fullmatch(path.name):
            errors.append(f'unexpected scene-like file: {path.name}')
        elif path.name not in expected:
            errors.append(f'unexpected scene id not in plan: {path.name}')
    return _result('scenes', errors, **extra)


def check_music(work_dir: Path, expected_music: int) -> dict:
    errors: list[str] = []
    expected = {f'music-{idx:03d}.md' for idx in range(1, expected_music + 1)}
    for name in sorted(expected):
        text = _read_nonempty(work_dir / name, errors, 'music file')
        if text is None:
            return _result('music', errors, expected=expected_music)
        missing = {'loop_index', 'cache_key'} - _frontmatter_fields(text)
        if missing:
            errors.append(f'{name} missing frontmatter field(s): {sorted(missing)}')
        if not _FRONTMATTER_RE.sub('', text, count=1).strip():
            errors.append(f'{name} has empty body')
        body = _FRONTMATTER_RE.sub('', text, count=1).strip()
        if '\n\nTags:' not in body:
            errors.append(f'{name} missing Tags line')
        if not re.search(r'\b(?:2-3|2 to 3)[ -]minute\b', body, re.IGNORECASE):
            errors.append(f'{name} missing 2-3 minute loop cue')
        if '--- LOOP' in body or '\nNegative:' in body or '\nLoop:' in body:
            errors.append(f'{name} uses obsolete music block format')

    for path in work_dir.glob('music-*.md'):
        if path.name == 'music-plan.md':
            continue
        if not _MUSIC_FILE_RE.fullmatch(path.name):
            errors.append(f'unexpected music-like file: {path.name}')
        elif path.name not in expected:
            errors.append(f'unexpected music id not expected: {path.name}')
    return _result('music', errors, expected=expected_music)


def _check_output_file(path: Path, marker: str, expected: int, errors: list[str]) -> bool:
    text = _read_nonempty(path, errors, 'output')
    if text is None:
        return False
    actual = text.count(marker)
    if actual != expected:
        errors.append(f'{path.name} has {actual} blocks, expected {expected}')
    return True


def check_outputs(input_path: Path, image_count: int, video_count: int, music_count: int) -> dict:
    errors: list[str] = []
    output_dir = input_path.parent
    stem = input_path.stem
    extra = {
        'image_count': image_count,
        'video_count': video_count,
        'music_count': music_count,
    }
    image_path = output_dir / f'{stem}_image_prompts.txt'
    video_path = output_dir / f'{stem}_video_prompts.txt'
    music_path = output_dir / f'{stem}_music_prompts.txt'
    if not _check_output_file(image_path, '--- SCENE ', image_count, errors):
        return _result('outputs', errors, **extra)
    if video_count > 0 and not _check_output_file(video_path, '--- SCENE ', video_count, errors):
        return _result('outputs', errors, **extra)
    if music_count > 0 and not _check_output_file(music_path, 'Tags:', music_count, errors):
        return _result('outputs', errors, **extra)
    return _result('outputs', errors, **extra)


def merge_results(results: list[dict]) -> dict:
    errors: list[str] = []
    for result in results:
        errors.extend(result.get('errors', []))
    return {'ok': not errors, 'results': results, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate visual-prompt artifacts')
    parser.add_argument('--check', choices=['scenes', 'music', 'outputs', 'all'], required=True)
    parser.add_argument('--work-dir', default=None)
    parser.add_argument('--scene-plan', default=None)
    parser.add_argument('--input', default=None)
    parser.add_argument('--expected-music', type=int, default=0)
    parser.add_argument('--image-count', type=int, default=0)
    parser.add_argument('--video-count', type=int, default=0)
    parser.add_argument('--music-count', type=int, default=0)
    args = parser.parse_args()

    work_dir = Path(args.work_dir) if args.work_dir else None
    results: list[dict] = []
    if args.check in {'scenes', 'all'}:
        if work_dir is None:
            raise SystemExit('--work-dir is required for scene validation')
        plan = Path(args.scene_plan) if args.scene_plan else work_dir / 'scene-plan.md'
        results.append(check_scenes(work_dir, plan))
    if args.check in {'music', 'all'}:
        if work_dir is None:
            raise SystemExit('--work-dir is required for music validation')
        results.append(check_music(work_dir, args.expected_music))
    if args.check in {'outputs', 'all'}:
        if not args.input:
            raise SystemExit('--input is required for output validation')
        results.append(check_outputs(Path(args.input), args.image_count, args.video_count, args.music_count))

    result = merge_results(results)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
