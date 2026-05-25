#!/usr/bin/env python3
"""v3.5 input loader — read .txt/.docx novel, detect chapter boundaries.

Output: JSON list of `{id, title, text}` to stdout for the agent loop.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CHAPTER_RE = re.compile(
    r'^[ \t]*(Chương|CHƯƠNG|Chapter|CHAPTER|chương|chapter)[ \t]+(\d+)[ \t:.\-—]*([^\n]*)$',
    re.MULTILINE,
)


def _read_txt(path: Path) -> str:
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'cp1252'):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding='utf-8', errors='replace')


def _read_docx(path: Path) -> str:
    try:
        from docx import Document  # type: ignore
    except ImportError as e:
        raise RuntimeError("python-docx not installed: pip install python-docx") from e
    doc = Document(str(path))
    return '\n\n'.join(p.text for p in doc.paragraphs if p.text)


def split_chapters(text: str) -> list[dict]:
    matches = list(CHAPTER_RE.finditer(text))
    if not matches:
        return [{'id': 1, 'title': 'Chương 1', 'text': text.strip()}]

    chapters: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        cid = int(m.group(2))
        title_tail = m.group(3).strip()
        title = f"Chương {cid}" + (f": {title_tail}" if title_tail else "")
        body = text[m.end():end].strip()
        chapters.append({'id': cid, 'title': title, 'text': body})
    return chapters


def load_input(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    raw = _read_docx(p) if p.suffix.lower() == '.docx' else _read_txt(p)
    return split_chapters(raw or '')


def main() -> int:
    parser = argparse.ArgumentParser(description='v3.5 input loader')
    parser.add_argument('input', help='Path to .txt or .docx novel file')
    args = parser.parse_args()
    chapters = load_input(args.input)
    print(json.dumps(chapters, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
