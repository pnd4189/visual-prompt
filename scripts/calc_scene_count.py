#!/usr/bin/env python3
"""Compute default image + video scene counts from a novel file.

Default formula:
    images = round(wordcount / 120)   (clamp to 120..150)
    videos = round(images   / 6)      (clamp >= 20)

CLI flags --images / --videos override; mixed overrides allowed.

Also emits a content-aware action_density signal (low/medium/high) from a cheap
combat-vocabulary scan, plus a recommended scene-mix band the planner consumes so
talky stories are not forced into a fake combat quota.

Output: JSON to stdout. Exit 0 success, 1 file not found.
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

from load_input import load_input  # type: ignore


def _wordcount_from_chapters(chapters: list[dict]) -> int:
    return sum(len(ch.get('text', '').split()) for ch in chapters)


# Combat / action vocabulary (xianxia/wuxia). Multi-word phrases are preferred to
# avoid false positives (e.g. "kiếm" alone also matches "tìm kiếm" = to search).
_COMBAT_KEYWORDS = [
    'giao chiến', 'trận pháp', 'phi kiếm', 'công kích', 'huyết chiến',
    'kiếm khí', 'kiếm quang', 'đại quân', 'ác chiến', 'truy sát', 'tấn công',
    'chiến đấu', 'vung kiếm', 'bao vây', 'đột kích', 'phản kích', 'chém giết',
    'kiếm trận', 'binh lính', 'quân đội', 'xáp lá cà', 'huyết quang',
    'chém', 'đâm', 'chiến', 'đánh nhau', 'giết',
]
_COMBAT_RE = re.compile(
    '|'.join(r'\b' + re.escape(k) + r'\b' for k in _COMBAT_KEYWORDS),
    re.IGNORECASE | re.UNICODE,
)


def _combat_hits(chapters: list[dict]) -> int:
    return sum(len(_COMBAT_RE.findall(ch.get('text', ''))) for ch in chapters)


def _classify_density(hits_per_1k: float) -> str:
    """Thresholds: low <2, medium 2-6, high >6 combat-hits per 1k words."""
    if hits_per_1k < 2:
        return 'low'
    if hits_per_1k <= 6:
        return 'medium'
    return 'high'


# Recommended scene-mix band per density. Action band is the only content-gated
# dimension; the v0.4 35-45% action figure now applies ONLY to high-density input.
_MIX_BANDS = {
    'low':    {'action': '5-15%',  'establishing': '25-35%', 'group': '20-30%', 'dialogue_emotional': 'remainder'},
    'medium': {'action': '20-30%', 'establishing': '25-35%', 'group': '15-25%', 'dialogue_emotional': 'remainder'},
    'high':   {'action': '35-45%', 'establishing': '20-30%', 'group': '15-25%', 'dialogue_emotional': 'remainder'},
}
# --epic raises the band one notch (amplify scale when the user wants it AND the
# story supports it). Never fabricates: the planner's no-fabrication rule still holds.
_EPIC_BUMP = {'low': 'medium', 'medium': 'high', 'high': 'high'}


def compute(wordcount: int, override_images: int | None, override_videos: int | None,
            combat_hits: int = 0, epic: bool = False) -> dict:
    auto_images = min(150, max(120, round(wordcount / 120)))
    auto_videos = max(20, round(auto_images / 6))

    images = override_images if override_images is not None else auto_images
    videos = override_videos if override_videos is not None else auto_videos

    if override_images is not None and override_videos is not None:
        source = 'override'
    elif override_images is None and override_videos is None:
        source = 'auto'
    else:
        source = 'mixed'

    hits_per_1k = (combat_hits / wordcount * 1000) if wordcount else 0.0
    density = _classify_density(hits_per_1k)
    band_key = _EPIC_BUMP[density] if epic else density

    return {
        'images': int(images),
        'videos': int(videos),
        'wordcount': int(wordcount),
        'source': source,
        'combat_hits': int(combat_hits),
        'combat_hits_per_1k': round(hits_per_1k, 2),
        'action_density': density,
        'epic': bool(epic),
        'recommended_mix': _MIX_BANDS[band_key],
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Scene count calculator')
    p.add_argument('--input', required=True, help='Path to novel file (.txt/.md/.docx)')
    p.add_argument('--images', type=int, default=None, help='Override image scene count')
    p.add_argument('--videos', type=int, default=None, help='Override video scene count')
    p.add_argument('--chapters-json', default=None,
                   help='Optional pre-computed chapters JSON path (default: load fresh)')
    p.add_argument('--epic', action='store_true',
                   help='Amplify scale: bump the recommended action band one notch')
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
    hits = _combat_hits(chapters)
    result = compute(wc, args.images, args.videos, combat_hits=hits, epic=args.epic)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
