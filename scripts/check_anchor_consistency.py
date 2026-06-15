#!/usr/bin/env python3
"""Verify (and optionally fix) that character identity anchors in an assembled
prompts file match the canonical character bible.

Why: the headless model sometimes expands prompts from a stale/wrong character
source, drifting a character's look across scenes (e.g. protagonist shown as
"20, grey robe" in some blocks and "16-17, armor" in others). Image generation
then produces an inconsistent character. The bible is the single source of truth;
this gate flags — and with --fix, normalizes — every off-bible anchor.

Anchor shape in output: "<name> — <age> years old, <build> build, ...<attire>."
We key off the age token right after the em dash, which is cheap and reliable.

Usage:
  check_anchor_consistency.py --bible <bible.md> --output <prompts.txt> [--fix]
Exit: 0 = consistent (or all fixed), 2 = violations remain, 1 = IO/parse error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AGE = r'[0-9][0-9\-–]*'  # 16-17, 20, 25-30 (hyphen or en-dash)


def parse_bible(text: str) -> dict[str, dict]:
    """name -> {age, anchor} from the markdown table rows."""
    chars: dict[str, dict] = {}
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) < 8 or cols[0].lower() == 'name' or cols[0].startswith('-'):
            continue
        name, age, build, hair, face, sig, attire = cols[:7]
        if not name or not re.match(AGE + r'$', age):
            continue
        anchor = (f"{name} — {age} years old, {build} build, {hair}, "
                  f"{face}, {sig}, {attire}.")
        chars[name] = {'age': age, 'anchor': anchor}
    return chars


def scan(text: str, chars: dict[str, dict]) -> dict[str, dict]:
    """name -> {good, bad:set(ages)} occurrence counts in the output."""
    report: dict[str, dict] = {}
    for name, info in chars.items():
        pat = re.compile(re.escape(name) + r'\s*—\s*(' + AGE + r')')
        good = bad = 0
        bad_ages: set[str] = set()
        for m in pat.finditer(text):
            if m.group(1) == info['age']:
                good += 1
            else:
                bad += 1
                bad_ages.add(m.group(1))
        if good or bad:
            report[name] = {'good': good, 'bad': bad, 'bad_ages': bad_ages}
    return report


def fix_text(text: str, chars: dict[str, dict]) -> tuple[str, int]:
    """Replace every off-bible anchor span '<name> — <age>...<.>' with canonical."""
    fixed = 0
    for name, info in chars.items():
        # match the whole anchor clause: name — <age> ... up to the first period
        pat = re.compile(re.escape(name) + r'\s*—\s*(' + AGE + r')[^.]*\.')

        def repl(m: re.Match) -> str:
            nonlocal fixed
            if m.group(1) == info['age']:
                return m.group(0)  # already canonical
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
            print(f"  {name}: {v['bad']} off-bible (ages {sorted(v['bad_ages'])}) "
                  f"vs {v['good']} canonical (bible age {chars[name]['age']})")
        return 2
    print(f"✓ anchors consistent with bible in {out_path.name}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
