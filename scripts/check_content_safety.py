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

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _io_utils import atomic_write_text, read_text_checked  # type: ignore

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
_NEGATIVE_FIELD_RE = re.compile(
    r'(?im)^[ \t]*(?:(?:[-*+]|#{1,6})[ \t]+)?\*{0,2}Negative\*{0,2}[ \t]*:',
)
_SECTION_BOUNDARY_RE = re.compile(
    r'(?m)^(?:---\s*SCENE\b|[ \t]*(?:[-*+][ \t]+)?\*{0,2}[A-Z][A-Za-z /&]{1,24}\*{0,2}[ \t]*:)',
)
_NEGATOR_BEFORE = re.compile(
    r'(?i)\b(?:no|not|avoid(?:ing)?|without|never|ban(?:ned)?)\b[\w\s/,-]{0,30}$')


def _is_negated(text: str, start: int) -> bool:
    """True if the match at `start` sits in an instruction telling the model to avoid it.

    Two shapes count. A per-item negator ("no gore", "avoiding blood") is caught
    by looking back a short way. A bare `Negative:` list (single-line or wrapped
    across lines) is also an avoid-list, so anything inside it up to the next
    section/scene boundary is negated.
    """
    line_start = text.rfind('\n', 0, start) + 1
    if _NEGATIVE_FIELD_RE.match(text, line_start):
        return True
    block_start = text.rfind('--- SCENE ', 0, start)
    block_start = 0 if block_start == -1 else block_start
    neg_matches = list(_NEGATIVE_FIELD_RE.finditer(text, block_start, start))
    if neg_matches:
        after_neg = neg_matches[-1].end()
        if not _SECTION_BOUNDARY_RE.search(text, after_neg, start):
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


# A hyphen is not a word character, so a blocked token matches inside a compound:
# "self-mutilated" hits on "mutilated". Detection is right to flag it — the phrase
# is gore either way — but replacing only the matched half left
# "gruesome self-no graphic blood enemy corpses" in a shipped file (observed
# 2026-08-14). The whole compound goes, or the sentence comes out broken.
_COMPOUND_EDGE_RE = re.compile(r'[\w]+(?:-[\w]+)*')


def _compound_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Widen a match to the hyphenated word it sits inside, if any."""
    left = start
    while left > 0 and (text[left - 1].isalnum() or text[left - 1] == '-'):
        left -= 1
    right = end
    while right < len(text) and (text[right].isalnum() or text[right] == '-'):
        right += 1
    return left, right


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

            def replace_all(source: str) -> str:
                out, cursor = [], 0
                for m in pat.finditer(source):
                    if m.start() < cursor:
                        continue
                    left, right = _compound_span(source, m.start(), m.end())
                    out.append(source[cursor:left])
                    out.append(sub(m) if (left, right) == (m.start(), m.end())
                               else (repl if sub(m) != m.group(0) else source[left:right]))
                    cursor = right
                out.append(source[cursor:])
                return ''.join(out)

            text = replace_all(text)
    return _clean_artifacts(text), fixed


def main() -> int:
    ap = argparse.ArgumentParser(description='Content-safety gate for assembled '
                                             'visual-prompt output files.')
    ap.add_argument('--output', required=False, default=None, help='assembled prompts .txt to scan')
    ap.add_argument('positional_output', nargs='?', default=None, help='assembled prompts .txt to scan (positional)')
    ap.add_argument('--blocklist', required=False, default=None, help='blocklist-content-safety.md')
    ap.add_argument('--fix', action='store_true', help='strip/soften in place')
    args = ap.parse_args()

    out_file = args.output or args.positional_output
    if not out_file:
        ap.error("the following arguments are required: --output or positional output")

    blocklist_file = args.blocklist
    if not blocklist_file:
        default_blocklist = Path(__file__).resolve().parent.parent / 'references' / 'blocklist-content-safety.md'
        if default_blocklist.is_file():
            blocklist_file = str(default_blocklist)
        else:
            ap.error("the following arguments are required: --blocklist")

    try:
        blocklist = read_text_checked(Path(blocklist_file))
        out_path = Path(out_file)
        text = read_text_checked(out_path)
    except (OSError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    rules = parse_blocklist(blocklist)
    if not rules:
        print(f"ERROR: no rules parsed from {blocklist_file}", file=sys.stderr)
        return 1

    if args.fix:
        text, n = fix_text(text, rules)
        if n:
            atomic_write_text(out_path, text)
        print(f"content-safety-fix: stripped {n} span(s) in {out_path.name}")

    hits = scan(text, rules)
    if hits:
        print(f"⚠ content-safety hits in {out_path.name}:")
        for section, found in hits.items():
            tag = ' (WARN-only)' if section in WARN_ONLY else ''
            print(f"  {section}{tag}: {len(found)} → {sorted(set(found))}")
        blocking = {sec: found for sec, found in hits.items() if sec not in WARN_ONLY}
        return 2 if blocking else 0
    print(f"✓ content-safe: {out_path.name}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
