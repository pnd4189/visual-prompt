#!/usr/bin/env python3
"""Verify (and optionally fix) that character identity anchors in an assembled
prompts file match the canonical character bible.

Why: the headless model sometimes expands prompts from a stale/wrong character
source, drifting a character's look across scenes (e.g. protagonist shown as
"20, grey robe" in some blocks and "16-17, armor" in others). Image generation
then produces an inconsistent character. The bible is the single source of truth;
this gate flags — and with --fix, normalizes — every off-bible anchor.

Anchor shape in output is derived from all seven identity fields. Unknown source
facts remain explicit `not stated` clauses instead of being visually invented.

Usage:
  check_anchor_consistency.py --bible <bible.md> --output <prompts.txt> [--fix]
Exit: 0 = consistent (or all fixed), 2 = violations remain, 1 = IO/parse error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AGE_RE = re.compile(r'[0-9][0-9\-–]*$')  # 16-17, 20, 25-30
UNKNOWN = {'', 'not stated'}


def _canonical_anchor(fields: list[str]) -> str:
    name, age, build, hair, face, signature, attire = fields[:7]
    if age.casefold() in UNKNOWN:
        age_clause = 'age not stated'
    elif AGE_RE.fullmatch(age):
        age_clause = f'{age} years old'
    else:
        age_clause = f'age described as {age}'
    build_clause = (
        'build not stated'
        if build.casefold() in UNKNOWN
        else f'{build} build'
    )
    hair_clause = 'hair not stated' if hair.casefold() in UNKNOWN else hair
    face_clause = 'face not stated' if face.casefold() in UNKNOWN else face
    signature_clause = (
        'signature mark not stated'
        if signature.casefold() in UNKNOWN
        else signature
    )
    attire_clause = 'attire not stated' if attire.casefold() in UNKNOWN else attire
    return (
        f'{name} — {age_clause}, {build_clause}, {hair_clause}, {face_clause}, '
        f'{signature_clause}, {attire_clause}.'
    )


def _normalized(value: str) -> str:
    return ' '.join(value.split())


def parse_bible(text: str) -> dict[str, dict]:
    """Return canonical, source-honest anchors from markdown table rows."""
    chars: dict[str, dict] = {}
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) < 8 or cols[0].lower() == 'name' or cols[0].startswith('-'):
            continue
        name = cols[0]
        if not name:
            continue
        chars[name] = {'anchor': _canonical_anchor(cols)}
    return chars


def scan(text: str, chars: dict[str, dict]) -> dict[str, dict]:
    """Count canonical and off-bible identity blocks for each character."""
    report: dict[str, dict] = {}
    for name, info in chars.items():
        pat = re.compile(re.escape(name) + r'\s*—\s*[^.]*\.', re.DOTALL)
        good = bad = 0
        for m in pat.finditer(text):
            if _normalized(m.group(0)) == _normalized(info['anchor']):
                good += 1
            else:
                bad += 1
        if good or bad:
            report[name] = {'good': good, 'bad': bad}
    return report


def fix_text(text: str, chars: dict[str, dict]) -> tuple[str, int]:
    """Replace every off-bible identity block with its canonical anchor."""
    fixed = 0
    for name, info in chars.items():
        pat = re.compile(re.escape(name) + r'\s*—\s*[^.]*\.', re.DOTALL)

        def repl(m: re.Match) -> str:
            nonlocal fixed
            if _normalized(m.group(0)) == _normalized(info['anchor']):
                return m.group(0)
            fixed += 1
            return info['anchor']

        text = pat.sub(repl, text)
    return text, fixed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bible', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--fix', action='store_true')
    args = ap.parse_args()

    try:
        bible = Path(args.bible).read_text(encoding='utf-8')
        out_path = Path(args.output)
        text = out_path.read_text(encoding='utf-8')
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    chars = parse_bible(bible)
    if not chars:
        print(f"ERROR: no characters parsed from {args.bible}", file=sys.stderr)
        return 1

    if args.fix:
        text, n = fix_text(text, chars)
        if n:
            out_path.write_text(text, encoding='utf-8')
        print(f"anchor-fix: normalized {n} off-bible anchor(s) in {out_path.name}")

    report = scan(text, chars)
    violations = {k: v for k, v in report.items() if v['bad']}
    if violations:
        print(f"⚠ anchor drift in {out_path.name}:")
        for name, v in violations.items():
            print(
                f"  {name}: {v['bad']} off-bible vs "
                f"{v['good']} canonical anchor(s)"
            )
        return 2
    print(f"✓ anchors consistent with bible in {out_path.name}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
