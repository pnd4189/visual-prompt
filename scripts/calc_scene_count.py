#!/usr/bin/env python3
"""Compute default image + video scene counts from a novel file.

Default formula:
    images = round(wordcount / 200)   (clamp >= 5)
    videos = round(images   / 7)      (clamp >= 2)

CLI flags --images / --videos override; mixed overrides allowed.

Output: JSON to stdout. Exit 0 success, 1 file not found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from load_input import load_input  # type: ignore


def _wordcount_from_chapters(chapters: list[dict]) -> int:
    return sum(len(ch.get('text', '').split()) for ch in chapters)


def compute(wordcount: int, override_images: int | None, override_videos: int | None) -> dict:
    auto_images = max(5, round(wordcount / 200))
    auto_videos = max(2, round(auto_images / 7))

    images = override_images if override_images is not None else auto_images
    videos = override_videos if override_videos is not None else auto_videos

    if override_images is not None and override_videos is not None:
        source = 'override'
    elif override_images is None and override_videos is None:
        source = 'auto'
    else:
        source = 'mixed'

    return {
        'images': int(images),
        'videos': int(videos),
        'wordcount': int(wordcount),
        'source': source,
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Scene count calculator')
    p.add_argument('--input', required=True, help='Path to novel file (.txt/.md/.docx)')
    p.add_argument('--images', type=int, default=None, help='Override image scene count')
    p.add_argument('--videos', type=int, default=None, help='Override video scene count')
    p.add_argument('--chapters-json', default=None,
                   help='Optional pre-computed chapters JSON path (default: load fresh)')
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        return 1

    if args.chapters_json and Path(args.chapters_json).exists():
        chapters = json.loads(Path(args.chapters_json).read_text(encoding='utf-8'))
    else:
        chapters = load_input(input_path)

    wc = _wordcount_from_chapters(chapters)
    result = compute(wc, args.images, args.videos)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
