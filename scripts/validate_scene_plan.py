#!/usr/bin/env python3
"""Grounding and variation gate for `.work/scene-plan.md`.

Every row carries an exact source anchor and explicit camera/action/palette plans.
This makes hallucinated beats and mechanical visual repetition fail before prompt
expansion.

Output JSON to stdout: {total, violations: [{type, scene_ids, reason}], ok}.
Exit 0 if ok, 2 if violations, 1 on IO error.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from calc_scene_count import deterministic_images  # type: ignore  # noqa: E402

MIN_SYNOPSIS_WORDS = 4
SYNOPSIS_SIMILARITY_THRESHOLD = 0.80
MIN_ANCHOR_WORDS = 6
MAX_ANCHOR_WORDS = 24
DIMENSION_SIMILARITY_THRESHOLD = 0.88

_ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')
_TOTALS_RE = re.compile(
    r'^Genre:\s*(?P<genre>.+?)\s+·\s+Images:\s*(?P<images>\d+)'
    r'\s+·\s+Videos:\s*(?P<videos>\d+)\s+·\s+Chapters:\s*(?P<chapters>\d+)\s*$',
    re.MULTILINE,
)
# How far a chapter's row share may sit from its share of the words. Calibrated
# once against a single collapsed plan (0.39x starved, 2.11x hogging) and set at
# 0.5-2.0, which then passed a healthy 15-chapter plan by 0.02: its quietest
# chapter came in at 0.52x. The two runs are only 0.13 apart at the low end, so
# this ratio cannot separate "collapsed" from "a long chapter that is mostly
# dialogue" — a talky chapter earns fewer visual beats than its word count says.
# Widened to catch only unmistakable collapse. The plan's declared totals are the
# real detectors: every gate fired on that bad plan, this one merely fourth.
CHAPTER_SHARE_MAX = 3.0
CHAPTER_SHARE_MIN = 0.34
# Below this, one row moves the share too much for the ratio to mean anything.
MIN_ROWS_FOR_BALANCE = 12
MIN_ROWS_OFF_BALANCE = 5
_PLAN_COLUMNS = (
    'scene_id', 'chapter', 'source_anchor', 'scene_tag', 'characters',
    'synopsis', 'setting_plan', 'camera_plan', 'action_plan', 'palette_plan',
    'video?',
)


def _split_row(line: str) -> list[str] | None:
    m = _ROW_RE.match(line)
    if not m:
        return None
    return [c.strip() for c in m.group(1).split('|')]


def parse_plan_contract(text: str) -> tuple[list[dict], list[str], dict | None]:
    """Parse the declared totals and strict grounded scene table."""
    rows: list[dict] = []
    errors: list[str] = []
    totals_match = _TOTALS_RE.search(text)
    totals = None
    if totals_match:
        totals = {
            'genre': totals_match.group('genre').strip(),
            'images': int(totals_match.group('images')),
            'videos': int(totals_match.group('videos')),
            'chapters': int(totals_match.group('chapters')),
        }
        if totals['images'] < 1:
            errors.append('declared Images must be at least 1')
        if totals['videos'] < 0 or totals['videos'] > totals['images']:
            errors.append('declared Videos must be between 0 and Images')
        if totals['chapters'] < 1:
            errors.append('declared Chapters must be at least 1')
    else:
        errors.append('missing strict Genre/Images/Videos/Chapters totals line')

    table_started = False
    for line_number, line in enumerate(text.splitlines(), 1):
        cells = _split_row(line)
        if not cells:
            continue
        normalized = tuple(cell.casefold() for cell in cells)
        if normalized == _PLAN_COLUMNS:
            if table_started:
                errors.append(f'line {line_number}: duplicate scene table header')
            table_started = True
            continue
        if not table_started:
            continue
        if all(cell and set(cell) <= {'-', ':'} for cell in cells):
            if len(cells) != len(_PLAN_COLUMNS):
                errors.append(
                    f'line {line_number}: scene separator must have '
                    f'{len(_PLAN_COLUMNS)} columns'
                )
            continue
        if len(cells) != len(_PLAN_COLUMNS):
            errors.append(
                f'line {line_number}: scene row must have '
                f'{len(_PLAN_COLUMNS)} columns'
            )
            continue
        scene_id = cells[0]
        if not re.fullmatch(r'\d+[a-zA-Z]?', scene_id):
            errors.append(f'line {line_number}: invalid scene_id {scene_id or "<empty>"}')
            continue
        if not cells[1].isdigit() or int(cells[1]) < 1:
            errors.append(f'line {line_number}: chapter must be a positive integer')
            continue
        required = {
            'source_anchor': cells[2],
            'scene_tag': cells[3],
            'synopsis': cells[5],
            'setting_plan': cells[6],
            'camera_plan': cells[7],
            'action_plan': cells[8],
            'palette_plan': cells[9],
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            errors.append(
                f'line {line_number}: required field(s) empty: {", ".join(missing)}'
            )
            continue
        if cells[10] not in {'', '✓'}:
            errors.append(f'line {line_number}: video? must be empty or ✓')
            continue
        chars = {c.strip() for c in cells[4].split(',') if c.strip()}
        rows.append({
            'scene_id': scene_id,
            'chapter': cells[1],
            'source_anchor': cells[2],
            'scene_tag': cells[3],
            'characters': chars,
            'synopsis': cells[5],
            'setting_plan': cells[6],
            'camera_plan': cells[7],
            'action_plan': cells[8],
            'palette_plan': cells[9],
            'has_video': cells[10] == '✓',
        })
    if not table_started:
        errors.append('missing exact scene table header')
    if not rows:
        errors.append('scene table contains no valid rows')
    if totals is not None:
        if len(rows) != totals['images']:
            errors.append(
                f'parsed scene count {len(rows)} does not match declared Images {totals["images"]}'
            )
        video_count = sum(row['has_video'] for row in rows)
        if video_count != totals['videos']:
            errors.append(
                f'parsed video count {video_count} does not match declared Videos {totals["videos"]}'
            )
    return rows, errors, totals


def parse_plan(text: str) -> list[dict]:
    """Return valid rows for callers that only need scene content."""
    rows, _, _ = parse_plan_contract(text)
    return rows


def check_scene_ids(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    violations = []
    order_keys: list[tuple[int, str]] = []
    for row in rows:
        match = re.fullmatch(r'(\d+)([a-zA-Z]?)', row['scene_id'])
        scene_id = (
            f'{int(match.group(1)):03d}{match.group(2).casefold()}'
            if match else row['scene_id'].casefold()
        )
        if match:
            order_keys.append((int(match.group(1)), match.group(2).casefold()))
        if scene_id in seen:
            violations.append({
                'type': 'duplicate_scene_id',
                'scene_ids': [row['scene_id']],
                'reason': 'scene id duplicates another row case-insensitively',
            })
        seen.add(scene_id)
    if order_keys != sorted(order_keys):
        violations.append({
            'type': 'scene_order',
            'scene_ids': [row['scene_id'] for row in rows],
            'reason': 'scene ids are not ordered from earliest to latest',
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


def check_synopsis_duplicates(rows: list[dict]) -> list[dict]:
    """Flag near-identical scene beats anywhere in the complete plan."""
    violations: list[dict] = []
    normalized = [' '.join(row['synopsis'].casefold().split()) for row in rows]
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            matcher = difflib.SequenceMatcher(None, normalized[left], normalized[right])
            if matcher.quick_ratio() < SYNOPSIS_SIMILARITY_THRESHOLD:
                continue
            ratio = matcher.ratio()
            if ratio >= SYNOPSIS_SIMILARITY_THRESHOLD:
                violations.append({
                    'type': 'duplicate_synopsis',
                    'scene_ids': [rows[left]['scene_id'], rows[right]['scene_id']],
                    'reason': (
                        f"synopsis {ratio:.0%} similar to scene {rows[left]['scene_id']} "
                        f"— rewrite this beat with a different moment/angle"
                    ),
                })
    return violations


def _normalize(value: str) -> str:
    return ' '.join(value.casefold().split())


def check_grounding(rows: list[dict], chapters: list[dict]) -> list[dict]:
    """Verify each scene beat against the QA'd chapter it references."""
    violations: list[dict] = []
    chapter_text = {
        str(chapter.get('id')): _normalize(str(chapter.get('text', '')))
        for chapter in chapters
        if chapter.get('id') is not None
    }
    previous_chapter = -1
    previous_anchor_position = -1
    for row in rows:
        scene_ids = [row['scene_id']]
        source = chapter_text.get(row['chapter'])
        if source is None:
            violations.append({
                'type': 'missing_source_chapter',
                'scene_ids': scene_ids,
                'reason': f"chapter {row['chapter']} does not exist in chapters_qa.json",
            })
            continue
        chapter_id = int(row['chapter'])
        if chapter_id < previous_chapter:
            violations.append({
                'type': 'story_order',
                'scene_ids': scene_ids,
                'reason': (
                    f'chapter {chapter_id} appears after chapter {previous_chapter}'
                ),
            })
        if chapter_id != previous_chapter:
            previous_anchor_position = -1
        anchor = _normalize(row['source_anchor'])
        word_count = len(anchor.split())
        if not MIN_ANCHOR_WORDS <= word_count <= MAX_ANCHOR_WORDS:
            violations.append({
                'type': 'invalid_source_anchor',
                'scene_ids': scene_ids,
                'reason': (
                    f'source_anchor has {word_count} words; expected '
                    f'{MIN_ANCHOR_WORDS}-{MAX_ANCHOR_WORDS}'
                ),
            })
        elif anchor not in source:
            violations.append({
                'type': 'ungrounded_source_anchor',
                'scene_ids': scene_ids,
                'reason': (
                    f"source_anchor is not an exact excerpt of chapter {row['chapter']}"
                ),
            })
        else:
            anchor_position = source.find(anchor)
            if anchor_position < previous_anchor_position:
                violations.append({
                    'type': 'story_order',
                    'scene_ids': scene_ids,
                    'reason': (
                        f"source_anchor goes backward inside chapter {row['chapter']}"
                    ),
                })
            previous_anchor_position = max(previous_anchor_position, anchor_position)
        for character in sorted(row['characters']):
            normalized_character = _normalize(character)
            if normalized_character and normalized_character not in source:
                violations.append({
                    'type': 'ungrounded_character',
                    'scene_ids': scene_ids,
                    'reason': (
                        f"character/group '{character}' is not named in "
                        f"chapter {row['chapter']}"
                    ),
                })
        previous_chapter = max(previous_chapter, chapter_id)
    return violations


def check_visual_dimensions(rows: list[dict]) -> list[dict]:
    """Reject exact adjacent reuse and three-scene near-identical visual runs."""
    violations: list[dict] = []
    dimensions = ('setting_plan', 'camera_plan', 'action_plan', 'palette_plan')
    for left, right in zip(rows, rows[1:]):
        for field in dimensions:
            if _normalize(left[field]) == _normalize(right[field]):
                violations.append({
                    'type': 'adjacent_visual_repeat',
                    'scene_ids': [left['scene_id'], right['scene_id']],
                    'reason': f'{field} is exactly repeated in adjacent scenes',
                })
    for index in range(len(rows) - 2):
        trio = rows[index:index + 3]
        for field in dimensions:
            values = [_normalize(row[field]) for row in trio]
            scores = [
                difflib.SequenceMatcher(None, values[0], values[1]).ratio(),
                difflib.SequenceMatcher(None, values[1], values[2]).ratio(),
            ]
            if min(scores) >= DIMENSION_SIMILARITY_THRESHOLD:
                violations.append({
                    'type': 'visual_dimension_monotony',
                    'scene_ids': [row['scene_id'] for row in trio],
                    'reason': (
                        f'{field} stays near-identical for three scenes '
                        f'(similarity >= {DIMENSION_SIMILARITY_THRESHOLD:.0%})'
                    ),
                })
    return violations


def check_declared_total(totals: dict | None, expected: int) -> list[dict]:
    """Hold the plan to the deterministic scene count, not to its own header.

    The row-count check above only compares the table against the `Images: N`
    line — and the model writes both. A run that quietly plans fewer beats than
    calc_scene_count settled on stays self-consistent and passes, which is how a
    150-image run shipped 114 (observed 2026-08-10). Compare against the formula.
    """
    if totals is None or totals['images'] == expected:
        return []
    return [{
        'type': 'scene_count_mismatch', 'scene_ids': [],
        'reason': (f'declared Images {totals["images"]} does not match the '
                   f'deterministic scene count {expected}'),
    }]


def check_declared_chapters(totals: dict | None, chapters: list[dict]) -> list[dict]:
    """`Chapters: K` counts the chapters, not the highest chapter label.

    A run over chapters 5-8 declared `Chapters: 8` (observed 2026-08-10). Nothing
    read the field, so the header drifted from the source it claims to describe.
    """
    if totals is None or totals['chapters'] == len(chapters):
        return []
    return [{
        'type': 'declared_chapters_mismatch', 'scene_ids': [],
        'reason': (f'declared Chapters {totals["chapters"]} does not match the '
                   f'{len(chapters)} chapters in the source'),
    }]


def check_declared_genre(totals: dict | None, genre: str | None) -> list[dict]:
    """The header genre must stay the genre the run locked its style to.

    The same run started at `đô thị` and ended declaring `Xianxia / Fantasy`,
    while the style block underneath it was still the one picked for `đô thị`.
    """
    if totals is None or not genre:
        return []
    if totals['genre'].casefold() == genre.strip().casefold():
        return []
    return [{
        'type': 'declared_genre_mismatch', 'scene_ids': [],
        'reason': (f'declared Genre "{totals["genre"]}" does not match the '
                   f'run genre "{genre.strip()}" in genre.txt'),
    }]


def check_chapter_balance(rows: list[dict], chapters: list[dict]) -> list[dict]:
    """Scene coverage should track each chapter's share of the prose.

    The planner contract asks for proportional coverage but nothing measured it:
    one run put 52% of its scenes in one of four near-equal chapters and gave
    another 10%. The band is deliberately loose — this catches a collapsed plan,
    not an uneven one.
    """
    words = {str(ch.get('id')): len(ch.get('text', '').split()) for ch in chapters}
    total_words = sum(words.values())
    if len(rows) < MIN_ROWS_FOR_BALANCE or total_words == 0 or len(words) < 2:
        return []

    counts: dict[str, int] = {}
    for row in rows:
        counts[row['chapter']] = counts.get(row['chapter'], 0) + 1

    violations = []
    for chapter_id, chapter_words in sorted(words.items()):
        if not chapter_words:
            continue
        expected = len(rows) * chapter_words / total_words
        actual = counts.get(chapter_id, 0)
        if abs(actual - expected) < MIN_ROWS_OFF_BALANCE:
            continue
        ratio = actual / expected
        if CHAPTER_SHARE_MIN <= ratio <= CHAPTER_SHARE_MAX:
            continue
        direction = 'over' if ratio > CHAPTER_SHARE_MAX else 'under'
        violations.append({
            'type': 'chapter_coverage_imbalance', 'scene_ids': [],
            'reason': (f'chapter {chapter_id} is {direction}-covered: {actual} rows '
                       f'against {expected:.0f} expected from its share of the prose '
                       f'({ratio:.2f}x)'),
        })
    return violations


def validate(text: str, chapters: list[dict] | None = None,
             expected_images: int | None = None, genre: str | None = None) -> dict:
    rows, contract_errors, totals = parse_plan_contract(text)
    violations = [
        {'type': 'malformed_plan', 'scene_ids': [], 'reason': error}
        for error in contract_errors
    ] + (
        check_scene_ids(rows)
        + check_synopsis(rows)
        + check_synopsis_duplicates(rows)
        + check_visual_dimensions(rows)
    )
    if expected_images is not None:
        violations.extend(check_declared_total(totals, expected_images))
    violations.extend(check_declared_genre(totals, genre))
    if chapters is not None:
        violations.extend(check_declared_chapters(totals, chapters))
        violations.extend(check_chapter_balance(rows, chapters))
        violations.extend(check_grounding(rows, chapters))
    return {
        'total': len(rows),
        'declared': totals,
        'violations': violations,
        'ok': not violations,
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description='Validate scene-plan grounding, schema, and visual variation'
    )
    p.add_argument('--plan', required=True, help='Path to .work/scene-plan.md')
    p.add_argument(
        '--chapters-json', required=True,
        help='Path to the QA chapter source used by the planner',
    )
    p.add_argument(
        '--expect-images', type=int, default=None,
        help='Image total for a run whose invocation overrode it with --images; '
             'omit so the deterministic count is recomputed from the chapters',
    )
    args = p.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"ERROR: scene plan not found: {plan_path}", file=sys.stderr)
        return 1

    chapters_path = Path(args.chapters_json)
    if not chapters_path.exists():
        print(f"ERROR: chapter source not found: {chapters_path}", file=sys.stderr)
        return 1
    try:
        chapters = json.loads(chapters_path.read_text(encoding='utf-8'))
        if not isinstance(chapters, list):
            raise ValueError('chapter source must be a JSON list')
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read chapter source: {exc}", file=sys.stderr)
        return 1

    expected = args.expect_images
    if expected is None:
        try:
            expected = deterministic_images(chapters)
        except (TypeError, AttributeError, ValueError) as exc:
            print(f"ERROR: cannot derive the scene count: {exc}", file=sys.stderr)
            return 1

    genre_path = plan_path.parent / 'genre.txt'
    try:
        genre = genre_path.read_text(encoding='utf-8').strip()
    except (OSError, UnicodeError):
        genre = None

    plan_bytes = plan_path.read_bytes()
    result = validate(plan_bytes.decode('utf-8'), chapters, expected, genre)
    if result['ok']:
        # The cache key the music path reads. Writing it here, from the bytes the
        # gate just accepted, retires a hand-computed step the model kept skipping.
        (plan_path.parent / 'plan.hash').write_text(
            hashlib.sha1(plan_bytes).hexdigest()[:12] + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
