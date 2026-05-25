#!/usr/bin/env python3
"""Assemble final image + video prompt .txt files from per-scene markdown.

Reads `<work-dir>/scene-*.md` (each with frontmatter + `## Image Prompt` and
optional `## Video Prompt` blocks).

Writes next to the input:
    <input-stem>_image_prompts.txt
    <input-stem>_video_prompts.txt

Separator uses ORIGINAL scene index so video file shows gaps:
    --- SCENE 007 ---
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _io_utils import atomic_write_text  # type: ignore

_SCENE_NUM_RE = re.compile(r'scene-(\d+)\.md$')
_MUSIC_NUM_RE = re.compile(r'music-(\d+)\.md$')
_IMAGE_RE = re.compile(
    r'^##\s*Image\s+Prompt\s*\n(.*?)(?=^##\s|\Z)', re.DOTALL | re.MULTILINE
)
_VIDEO_RE = re.compile(
    r'^##\s*Video\s+Prompt\s*\n(.*?)(?=^##\s|\Z)', re.DOTALL | re.MULTILINE
)
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def _scene_num(path: Path) -> int:
    m = _SCENE_NUM_RE.search(path.name)
    return int(m.group(1)) if m else 0


def discover_scenes(work_dir: Path) -> list[Path]:
    return sorted(work_dir.glob('scene-*.md'), key=_scene_num)


def _music_num(path: Path) -> int:
    m = _MUSIC_NUM_RE.search(path.name)
    return int(m.group(1)) if m else 0


def discover_music(work_dir: Path) -> list[Path]:
    return sorted(work_dir.glob('music-*.md'), key=_music_num)


def parse_music(path: Path) -> dict:
    """The whole body after frontmatter is the Lyria prompt block (incl. label)."""
    text = path.read_text(encoding='utf-8')
    body = _FRONTMATTER_RE.sub('', text, count=1)
    return {
        'loop_index': _music_num(path),
        'body': body.strip(),
        'path': str(path),
    }


def parse_scene(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    body = _FRONTMATTER_RE.sub('', text, count=1)
    img_m = _IMAGE_RE.search(body)
    vid_m = _VIDEO_RE.search(body)
    return {
        'scene_id': _scene_num(path),
        'image': img_m.group(1).strip() if img_m else '',
        'video': vid_m.group(1).strip() if vid_m else '',
        'path': str(path),
    }


def assemble(input_path: Path, work_dir: Path) -> dict:
    scenes_paths = discover_scenes(work_dir)
    if not scenes_paths:
        raise RuntimeError(f"No scene-*.md found in {work_dir}")

    image_blocks: list[tuple[int, str]] = []
    video_blocks: list[tuple[int, str]] = []
    warnings: list[str] = []

    for sp in scenes_paths:
        sc = parse_scene(sp)
        if not sc['image']:
            warnings.append(f"scene-{sc['scene_id']:03d}.md missing '## Image Prompt' block — skipped")
            continue
        image_blocks.append((sc['scene_id'], sc['image']))
        if sc['video']:
            video_blocks.append((sc['scene_id'], sc['video']))

    def _join(blocks: list[tuple[int, str]]) -> str:
        parts = []
        for sid, body in blocks:
            parts.append(f"--- SCENE {sid:03d} ---\n\n{body}")
        return '\n\n'.join(parts)

    output_dir = input_path.parent
    stem = input_path.stem
    img_path = output_dir / f"{stem}_image_prompts.txt"
    vid_path = output_dir / f"{stem}_video_prompts.txt"

    atomic_write_text(img_path, _join(image_blocks))
    atomic_write_text(vid_path, _join(video_blocks))

    # Music is an independent code path: assemble only if regions exist.
    music_blocks: list[str] = []
    for mp in discover_music(work_dir):
        mc = parse_music(mp)
        if mc['body']:
            music_blocks.append(mc['body'])
        else:
            warnings.append(f"{mp.name} has empty body — skipped")

    music_path = None
    if music_blocks:
        music_path = output_dir / f"{stem}_music_prompts.txt"
        atomic_write_text(music_path, '\n\n'.join(music_blocks) + '\n')

    return {
        'image_count': len(image_blocks),
        'video_count': len(video_blocks),
        'video_indices': [sid for sid, _ in video_blocks],
        'image_path': str(img_path),
        'video_path': str(vid_path),
        'music_count': len(music_blocks),
        'music_path': str(music_path) if music_path else None,
        'warnings': warnings,
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Assemble final prompt .txt files')
    p.add_argument('--input', required=True,
                   help='Original novel file path (used to derive output stem + dir)')
    p.add_argument('--work-dir', default=None,
                   help='Dir containing scene-*.md (default: <input-dir>/.work)')
    args = p.parse_args()

    input_path = Path(args.input)
    work_dir = Path(args.work_dir) if args.work_dir else input_path.parent / '.work'

    try:
        summary = assemble(input_path, work_dir)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
