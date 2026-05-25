#!/usr/bin/env python3
"""Append a single character row to character-bible.md — append-only safety.

Why: LLM rewriting the whole bible risks byte-identity drift on existing rows.
This helper opens the file in append mode and only ever writes a new row,
so existing content stays byte-identical.

Row is plain text (typically a markdown table row or YAML list item). It is
NOT validated as YAML — bibles use markdown tables, not YAML.

If the file does not exist, it is created with the row alone.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def append_row(bible_path: Path, row: str) -> int:
    bible_path.parent.mkdir(parents=True, exist_ok=True)
    row = row.rstrip('\n')
    if not row.strip():
        raise ValueError("empty row")

    existing = bible_path.read_text(encoding='utf-8') if bible_path.exists() else ''
    sep = '' if existing.endswith('\n') or not existing else '\n'

    with open(bible_path, 'a', encoding='utf-8') as f:
        f.write(f"{sep}{row}\n")
        f.flush()
        os.fsync(f.fileno())

    # count rows = non-empty lines after header (rough)
    new_text = bible_path.read_text(encoding='utf-8')
    line_count = sum(1 for ln in new_text.splitlines() if ln.strip())
    return line_count


def main() -> int:
    p = argparse.ArgumentParser(description='Append one row to character bible')
    p.add_argument('--bible', required=True, help='Path to character-bible.md')
    p.add_argument('--row', required=True, help='Row string to append')
    args = p.parse_args()

    try:
        n = append_row(Path(args.bible), args.row)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Appended row to {args.bible} (file now ~{n} non-empty lines)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
