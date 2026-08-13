#!/usr/bin/env python3
"""Scan (and optionally fix) an assembled prompt file for content-safety
violations: named brands/IP, real-person likeness, excessive gore, sexual
content, real-religion desecration, and live-action/photoreal video.

Why: image/video prompts must stay copyright- and platform-policy-safe. The
headless model occasionally names a brand or a real actor, or drifts a video
prompt toward live-action realism. This deterministic gate flags — and with
--fix, strips/softens — those spans in the assembled .txt, mirroring
`check_anchor_consistency.py`. Religion is WARN-only (regex cannot judge
context, so it is reported but never auto-rewritten).

Blocklist data lives in `references/blocklist-content-safety.md`; see that file
for the line conventions (plain = literal whole-word; `re:` = regex).

Usage:
  check_content_safety.py --output <prompts.txt> --blocklist <md> [--fix]
Exit: 0 = clean (or all auto-fixable fixed), 2 = violations remain, 1 = IO/parse.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Replacement applied per section when --fix runs. Sections absent here are
# WARN-only (collected, never rewritten) — currently RELIGION_HIGH_RISK.
FIX_REPLACEMENT = {
    'BRANDS': '',
    'IP_CHARACTERS': '',
    'LIKENESS_TRIGGERS': '',
    'GORE': 'no graphic blood',
    'SEXUAL': 'modestly clothed',
    'PHOTOREAL_VIDEO': 'stylized animation',
}
WARN_ONLY = {'RELIGION_HIGH_RISK'}

# These categories name the SAME words used in `Negative:` / "avoiding …" safety
# instructions (e.g. "no nudity", "no graphic gore", "no live-action"). A hit in
# that prohibiting context is the rule working, not a violation — skip it so the
# gate never mangles its own safety line. Brand/IP/likeness/religion are NOT
# guarded (a named brand/person is a hit regardless of phrasing).
NEGATION_GUARDED = {'GORE', 'SEXUAL', 'PHOTOREAL_VIDEO'}
_NEGATIVE_FIELD_RE = re.compile(r'[ \t]*Negative[ \t]*:', re.IGNORECASE)
_NEGATOR_BEFORE = re.compile(
    r'(?i)\b(?:no|not|avoid(?:ing)?|without|never|ban(?:ned)?)\b[\w\s/,-]{0,30}$')


def _is_negated(text: str, start: int) -> bool:
    """True if the match at `start` sits in an instruction telling the model to avoid it.

    Two shapes count. A per-item negator ("no gore", "avoiding blood") is caught
    by looking back a short way. A bare `Negative:` list is not — one run wrote
    "…ugly, duplicate, morbid, mutilated, disfigured" with no "no" on any item,
    and every one of its 156 scenes was reported as a GORE hit (observed
    2026-08-13). The whole line is the avoid-list, so anything on it is negated.
    """
    line_start = text.rfind('\n', 0, start) + 1
    if _NEGATIVE_FIELD_RE.match(text, line_start):
        return True
    return bool(_NEGATOR_BEFORE.search(text[max(0, start - 40):start]))


def literal_to_regex(token: str) -> re.Pattern:
    """Whole-word, case-insensitive matcher for a literal token. Brand/IP tokens
    optionally consume a trailing ` logo`/` brand`/` trademark` so the fix removes
    the whole reference."""
    body = re.escape(token) + r'(?:\s+(?:logo|brand|trademark))?'
    return re.compile(r'(?<!\w)' + body + r'(?!\w)', re.IGNORECASE | re.UNICODE)


def parse_blocklist(text: str) -> dict[str, list[re.Pattern]]:
    """Parse the markdown blocklist into {SECTION: [compiled patterns]}."""
    rules: dict[str, list[re.Pattern]] = {}
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('<!--') or line.startswith('>'):
            continue
        if line.startswith('## '):
            section = line[3:].strip()
            rules.setdefault(section, [])
            continue
        if line.startswith('#') or section is None:
            continue  # title / pre-section prose
        if line.startswith('re:'):
            rules[section].append(re.compile(line[3:].strip()))
        else:
            rules[section].append(literal_to_regex(line))
    return {k: v for k, v in rules.items() if v}


def scan(text: str, rules: dict[str, list[re.Pattern]]) -> dict[str, list[str]]:
    """SECTION -> list of matched strings found in the text."""
    hits: dict[str, list[str]] = {}
    for section, patterns in rules.items():
        guarded = section in NEGATION_GUARDED
        for pat in patterns:
            for m in pat.finditer(text):
                if guarded and _is_negated(text, m.start()):
                    continue
                hits.setdefault(section, []).append(m.group(0).strip())
    return hits


def _clean_artifacts(text: str) -> str:
    """Tidy whitespace/comma artifacts left by deletions."""
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r',(\s*,)+', ',', text)
    text = re.sub(r'(?m)^[ \t]*,[ \t]*', '', text)
    return text


def fix_text(text: str, rules: dict[str, list[re.Pattern]]) -> tuple[str, int]:
    """Apply per-section replacements; return (new_text, count). WARN-only
    sections (religion) are left untouched."""
    fixed = 0
    for section, patterns in rules.items():
        if section in WARN_ONLY:
            continue
        repl = FIX_REPLACEMENT.get(section, '')
        guarded = section in NEGATION_GUARDED
        for pat in patterns:
            def sub(m: re.Match) -> str:
                nonlocal fixed
                if guarded and _is_negated(text, m.start()):
                    return m.group(0)  # prohibiting context — leave intact
                fixed += 1
                return repl
            text = pat.sub(sub, text)
    return _clean_artifacts(text), fixed


def main() -> int:
    ap = argparse.ArgumentParser(description='Content-safety gate for assembled '
                                             'visual-prompt output files.')
    ap.add_argument('--output', required=True, help='assembled prompts .txt to scan')
    ap.add_argument('--blocklist', required=True, help='blocklist-content-safety.md')
    ap.add_argument('--fix', action='store_true', help='strip/soften in place')
    args = ap.parse_args()

    try:
        blocklist = Path(args.blocklist).read_text(encoding='utf-8')
        out_path = Path(args.output)
        text = out_path.read_text(encoding='utf-8')
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    rules = parse_blocklist(blocklist)
    if not rules:
        print(f"ERROR: no rules parsed from {args.blocklist}", file=sys.stderr)
        return 1

    if args.fix:
        text, n = fix_text(text, rules)
        if n:
            out_path.write_text(text, encoding='utf-8')
        print(f"content-safety-fix: stripped {n} span(s) in {out_path.name}")

    hits = scan(text, rules)
    if hits:
        print(f"⚠ content-safety hits in {out_path.name}:")
        for section, found in hits.items():
            tag = ' (WARN-only)' if section in WARN_ONLY else ''
            print(f"  {section}{tag}: {len(found)} → {sorted(set(found))}")
        return 2
    print(f"✓ content-safe: {out_path.name}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
