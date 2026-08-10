#!/usr/bin/env python3
"""Compute image count and optional video count from a novel file.

Default formula:
    images = round(wordcount / 120)   (clamp to 120..300)
    videos = 0

When video is explicitly enabled:
    videos = round(images / 6)        (target >= 20, never above images)

CLI flags --images / --videos override; --video enables automatic video count.

Also emits an action_density signal (low/medium/high) from a cheap combat-vocab
scan. The planner may use it only as source metadata; it must not manufacture a
scene category to satisfy a quota.

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


MIN_IMAGES = 4
WORDS_PER_SCENE_FLOOR = 50
WORDS_PER_IMAGE = 120
BAND_FLOOR = 120
# A ~1.5h narration measured at 18.7k words, so a 3h episode lands near 37k words
# — one image per 120 words puts that at 300. Raising the ceiling lets a long
# source keep the same rhythm instead of thinning out across the same 150 beats.
BAND_CEILING = 300

_GROUNDED_MIX = {
    'action': 'source-supported only',
    'establishing': 'source-supported only',
    'group': 'source-supported only',
    'dialogue_emotional': 'source-supported only',
}


def compute(wordcount: int, override_images: int | None, override_videos: int | None,
            combat_hits: int = 0, epic: bool = False, faithful: bool = False,
            video_enabled: bool = False) -> dict:
    if override_images is not None and override_images < 1:
        raise ValueError('--images must be at least 1')
    if override_videos is not None and override_videos < 1:
        raise ValueError('--videos must be at least 1')
    # The 120..300 band assumes a full chapter file. A short source cannot ground
    # that many distinct scenes, so cap the band at one scene per 50 words —
    # asking for more forces the model to fabricate, pad, or halt on turn one.
    grounding_cap = max(MIN_IMAGES, wordcount // WORDS_PER_SCENE_FLOOR)
    auto_images = min(
        BAND_CEILING,
        max(BAND_FLOOR, round(wordcount / WORDS_PER_IMAGE)),
        grounding_cap,
    )
    images = override_images if override_images is not None else auto_images
    auto_videos = min(images, max(20, round(images / 6)))
    if override_videos is not None and override_videos > images:
        raise ValueError('--videos cannot exceed the effective image count')
    videos = (
        override_videos
        if override_videos is not None
        else auto_videos if video_enabled else 0
    )

    if override_images is not None and override_videos is not None:
        source = 'override'
    elif override_images is None and override_videos is None:
        source = 'auto'
    else:
        source = 'mixed'

    hits_per_1k = (combat_hits / wordcount * 1000) if wordcount else 0.0
    density = _classify_density(hits_per_1k)

    return {
        'images': int(images),
        'videos': int(videos),
        'wordcount': int(wordcount),
        'source': source,
        'combat_hits': int(combat_hits),
        'combat_hits_per_1k': round(hits_per_1k, 2),
        'action_density': density,
        'grounding_capped': bool(override_images is None and auto_images == grounding_cap
                                 and grounding_cap < BAND_FLOOR),
        'mode': 'grounded',
        'epic': bool(epic),
        'recommended_mix': _GROUNDED_MIX,
    }


def deterministic_images(chapters: list[dict]) -> int:
    """The deterministic image target for a chapter set.

    The scene-plan gate recomputes this from the same chapter source the planner
    read, so the declared total is checked against the formula rather than against
    the header the model wrote for itself.
    """
    return compute(
        _wordcount_from_chapters(chapters), None, None,
        combat_hits=_combat_hits(chapters),
    )['images']


def main() -> int:
    p = argparse.ArgumentParser(description='Scene count calculator')
    p.add_argument('--input', required=True, help='Path to novel file (.txt/.md/.docx)')
    p.add_argument('--images', type=int, default=None, help='Override image scene count')
    p.add_argument('--videos', type=int, default=None, help='Override video scene count')
    p.add_argument('--video', action='store_true',
                   help='Enable automatic video count when --videos is omitted')
    p.add_argument('--chapters-json', default=None,
                   help='Optional pre-computed chapters JSON path (default: load fresh)')
    p.add_argument('--epic', action='store_true',
                   help='Amplify scale: bump the recommended action band one notch')
    p.add_argument('--faithful', action='store_true',
                   help='Legacy compatibility flag; all runs are grounded')
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
    try:
        result = compute(
            wc, args.images, args.videos, combat_hits=hits,
            epic=args.epic, faithful=args.faithful,
            video_enabled=args.video,
        )
    except ValueError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
