#!/usr/bin/env python3
"""Plan-level variation gate for `.work/scene-plan.md`.

Deterministic backstop after Pass 1. Flags two monotony/quality problems so they
cannot pass silently into the expander:

1. Adjacent-duplicate scenes: a pair within a sliding window (default 10 indices)
   sharing the same scene_tag AND >70% character overlap. (Location is intentionally
   NOT used — deriving it from the synopsis is too noisy; tag+character is the firm
   signal per the plan.)
2. Invalid/fragment synopsis: empty, too short, or a raw text slice that starts
   mid-word (Vietnamese sentences start capitalized; a leading lowercase letter
   signals a sliced fragment).

Output JSON to stdout: {total, violations: [{type, scene_ids, reason}], ok}.
Exit 0 if ok, 2 if violations, 1 on IO error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WINDOW = 10
CHAR_OVERLAP_THRESHOLD = 0.70
MIN_SYNOPSIS_WORDS = 4

_ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')


def _split_row(line: str) -> list[str] | None:
    m = _ROW_RE.match(line)
    if not m:
        return None
    return [c.strip() for c in m.group(1).split('|')]


def parse_plan(text: str) -> list[dict]:
    """Parse the markdown scene table into row dicts. Robust to leading/trailing pipes."""
    rows: list[dict] = []
    for line in text.splitlines():
        cells = _split_row(line)
        if not cells or len(cells) < 6:
            continue
        scene_id = cells[0]
        # Skip header row and the |---|---| separator row.
        if scene_id.lower() == 'scene_id' or set(scene_id) <= {'-', ':'}:
            continue
        if not re.match(r'^\d+$', scene_id):
            continue
        chars = {c.strip() for c in cells[3].split(',') if c.strip()}
        rows.append({
            'scene_id': scene_id,
            'chapter': cells[1],
            'scene_tag': cells[2],
            'characters': chars,
            'synopsis': cells[4],
        })
    return rows


def _char_overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def check_duplicates(rows: list[dict]) -> list[dict]:
    violations: list[dict] = []
    for i, r in enumerate(rows):
        for j in range(i + 1, min(i + 1 + WINDOW, len(rows))):
            s = rows[j]
            if r['scene_tag'] != s['scene_tag']:
                continue
            overlap = _char_overlap(r['characters'], s['characters'])
            if overlap > CHAR_OVERLAP_THRESHOLD:
                violations.append({
                    'type': 'adjacent_duplicate',
                    'scene_ids': [r['scene_id'], s['scene_id']],
                    'reason': (
                        f"same tag '{r['scene_tag']}' + {overlap:.0%} character overlap "
                        f"within {WINDOW}-scene window"
                    ),
                })
    return violations


def _first_letter(s: str) -> str | None:
    """First alphabetic character after stripping leading quotes/punctuation/space."""
    stripped = s.lstrip('"\'`“”‘’ \t.,;:–-—…()[]')
    for ch in stripped:
        if ch.isalpha():
            return ch
    return None


def check_synopsis(rows: list[dict]) -> list[dict]:
    violations: list[dict] = []
    for r in rows:
        syn = r['synopsis'].strip()
        if not syn:
            violations.append({'type': 'fragment_synopsis', 'scene_ids': [r['scene_id']],
                               'reason': 'empty synopsis'})
            continue
        if len(syn.split()) < MIN_SYNOPSIS_WORDS:
            violations.append({'type': 'fragment_synopsis', 'scene_ids': [r['scene_id']],
                               'reason': f'too short (<{MIN_SYNOPSIS_WORDS} words)'})
            continue
        first = _first_letter(syn)
        if first is not None and first.islower():
            violations.append({'type': 'fragment_synopsis', 'scene_ids': [r['scene_id']],
                               'reason': 'starts mid-word (lowercase) — raw text slice'})
    return violations


def validate(text: str) -> dict:
    rows = parse_plan(text)
    violations = check_duplicates(rows) + check_synopsis(rows)
    return {'total': len(rows), 'violations': violations, 'ok': not violations}


def main() -> int:
    p = argparse.ArgumentParser(description='Validate a scene-plan.md for monotony + fragment synopses')
    p.add_argument('--plan', required=True, help='Path to .work/scene-plan.md')
    args = p.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"ERROR: scene plan not found: {plan_path}", file=sys.stderr)
        return 1

    result = validate(plan_path.read_text(encoding='utf-8'))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
