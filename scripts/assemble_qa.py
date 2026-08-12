#!/usr/bin/env python3
"""Assemble the QA'd source of truth from per-chapter proofread markdown.

Reads `<work-dir>/qa-chapter-*.md` (each with frontmatter `{chapter_id, title,
cache_key}` + body = corrected chapter prose).

Writes:
    <work-dir>/chapters_qa.json   — downstream source, schema {id, title, text}
    <input-dir>/<input-stem>_qa.txt — human-readable + TTS-ready

The `_qa.txt` chapter heading is rendered `Chương N: Title.` with a trailing
period so a TTS engine that splits on punctuation inserts a pause and does not
merge the title into the first sentence.
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

from _io_utils import atomic_write_json, atomic_write_text, read_text_checked  # type: ignore

_QA_NUM_RE = re.compile(r'qa-chapter-(\d+)\.md$')
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
_FM_FIELD_RE = re.compile(r'^([A-Za-z_]+):\s*(.*)$')


def _qa_num(path: Path) -> int:
    m = _QA_NUM_RE.search(path.name)
    return int(m.group(1)) if m else 0


def discover_qa(work_dir: Path) -> list[Path]:
    return sorted(work_dir.glob('qa-chapter-*.md'), key=_qa_num)


def _parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.search(text)
    if not m:
        return {}
    fields: dict = {}
    for line in m.group(1).splitlines():
        fm = _FM_FIELD_RE.match(line.strip())
        if fm:
            val = fm.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in '"\'':
                val = val[1:-1]
            fields[fm.group(1)] = val
    return fields


def parse_qa_chapter(path: Path) -> dict:
    text = read_text_checked(path)
    fm = _parse_frontmatter(text)
    body = _FRONTMATTER_RE.sub('', text, count=1).strip()
    fallback_id = _qa_num(path)
    try:
        cid = int(fm.get('chapter_id', fallback_id))
    except ValueError:
        cid = fallback_id
    return {
        'id': cid,
        'title': fm.get('title', f'Chương {cid}'),
        'text': body,
        'path': str(path),
    }


def _render_heading(title: str) -> str:
    """Render a chapter heading that ends with a terminal period for TTS pause."""
    heading = title.strip()
    if heading and heading[-1] not in '.!?。！？':
        heading += '.'
    return heading


# A proofread trims residue and splits sentences; it does not shorten the story.
# Measured on three healthy runs: 99.9%, 96.8% and 99.7% of the source words
# survived. A run that kept 36% had quietly truncated its later chapters — the
# first seven were near full length and the last eight collapsed to a fifth —
# and every downstream gate then agreed with the shortened text, because
# chapters_qa.json is what they all measure against (observed 2026-08-11).
MIN_QA_WORD_RETENTION = 0.85

# The total above stays healthy when a single chapter is gutted: one run kept 96%
# of the words overall while chapter 387 kept 54% — the second half of the chapter
# was gone and a fabricated closing line hid the seam (observed 2026-08-12). Length
# is therefore checked per chapter against chapters.json as well.
MIN_QA_CHAPTER_WORD_RETENTION = 0.85

# A chapter can also stop a few paragraphs early without losing enough words to
# trip either ratio: chapter 383 kept 96% of its words yet dropped the closing
# reveal, and the model wrote a fabricated line over the seam so the text still
# read as finished. So the last source paragraph has to survive somewhere in the
# last few QA paragraphs. Measured on this run: healthy chapters scored 0.97-1.00,
# the two truncated ones 0.27 and 0.31.
MIN_QA_ENDING_COVERAGE = 0.6

_TOKEN_RE = re.compile(r'\w+', re.UNICODE)


def _word_count(text: str) -> int:
    return len(text.split())


def _paragraphs(text: str) -> list[str]:
    return [p for p in text.split('\n') if p.strip()]


def _source_chapters(work_dir: Path) -> dict[int, str]:
    """Per-chapter source text from chapters.json; empty when it is unreadable."""
    path = work_dir / 'chapters.json'
    if not path.exists():
        return {}
    try:
        rows = json.loads(read_text_checked(path))
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError):
        return {}
    if not isinstance(rows, list):
        return {}
    return {int(row['id']): row.get('text', '')
            for row in rows if isinstance(row, dict) and 'id' in row}


def _ending_coverage(source_text: str, qa_text: str) -> float:
    """Share of the last source paragraph's words still present in the QA ending.

    Compares against the last three QA paragraphs, so a proofread that merges or
    splits the closing paragraphs still scores full coverage; only text that is
    gone scores low.
    """
    src_paras, qa_paras = _paragraphs(source_text), _paragraphs(qa_text)
    if not src_paras or not qa_paras:
        return 0.0
    wanted = set(_TOKEN_RE.findall(src_paras[-1].lower()))
    if not wanted:
        return 1.0
    tail = set(_TOKEN_RE.findall(' '.join(qa_paras[-3:]).lower()))
    return len(wanted & tail) / len(wanted)


def assemble(input_path: Path, work_dir: Path) -> dict:
    qa_paths = discover_qa(work_dir)
    if not qa_paths:
        raise RuntimeError(f"No qa-chapter-*.md found in {work_dir}")

    chapters: list[dict] = []
    txt_parts: list[str] = []
    warnings: list[str] = []
    seen_ids: set[int] = set()

    for qp in qa_paths:
        ch = parse_qa_chapter(qp)
        if ch['id'] in seen_ids:
            warnings.append(f"duplicate chapter id {ch['id']} in {qp.name} — kept both")
        seen_ids.add(ch['id'])
        if not ch['text']:
            warnings.append(f"{qp.name} has empty body after frontmatter")
        chapters.append({'id': ch['id'], 'title': ch['title'], 'text': ch['text']})
        txt_parts.append(f"{_render_heading(ch['title'])}\n\n{ch['text']}")

    # Gap detection: contiguous ids starting at the smallest seen id.
    ids = sorted(seen_ids)
    if ids:
        expected = set(range(ids[0], ids[-1] + 1))
        missing = sorted(expected - seen_ids)
        if missing:
            warnings.append(f"missing chapter ids: {missing}")

    # Refuse before writing: chapters_qa.json is the source every later gate
    # checks against, so a truncated one is agreed with rather than caught, and
    # <stem>_qa.txt is the text that becomes the audio.
    source_texts = _source_chapters(work_dir)
    if source_texts:
        gutted, truncated = [], []
        for chapter in chapters:
            source_text = source_texts.get(chapter['id'])
            if source_text is None:
                continue
            kept, src_words = _word_count(chapter['text']), _word_count(source_text)
            if kept < src_words * MIN_QA_CHAPTER_WORD_RETENTION:
                gutted.append(f"{chapter['id']} kept {kept}/{src_words} words")
            elif _ending_coverage(source_text, chapter['text']) < MIN_QA_ENDING_COVERAGE:
                truncated.append(str(chapter['id']))
        if gutted or truncated:
            detail = '; '.join(
                part for part in (
                    f"short chapters: {', '.join(gutted)}" if gutted else '',
                    f"chapters missing their ending: {', '.join(truncated)}" if truncated else '',
                ) if part
            )
            raise RuntimeError(
                f'QA dropped text inside {len(gutted) + len(truncated)} chapter(s) '
                f'({detail}). Proofreading does not shorten the story. Re-run the QA '
                f'loop for those chapters before assembling.'
            )
    else:
        warnings.append('chapters.json unreadable — per-chapter length check skipped')

    source_words = _word_count(read_text_checked(input_path))
    kept_words = sum(_word_count(chapter['text']) for chapter in chapters)
    if source_words and kept_words < source_words * MIN_QA_WORD_RETENTION:
        short = sorted(
            ((chapter['id'], _word_count(chapter['text'])) for chapter in chapters),
            key=lambda pair: pair[1],
        )[:5]
        raise RuntimeError(
            f'QA kept {kept_words} of {source_words} source words '
            f'({kept_words / source_words:.0%}); proofreading does not shorten the '
            f'story. Shortest chapters: {short}. Re-run the QA loop for those '
            f'chapters before assembling.'
        )

    work_dir.mkdir(parents=True, exist_ok=True)
    qa_json_path = work_dir / 'chapters_qa.json'
    qa_txt_path = input_path.parent / f"{input_path.stem}_qa.txt"

    atomic_write_json(qa_json_path, chapters, ensure_ascii=False)
    atomic_write_text(qa_txt_path, '\n\n'.join(txt_parts) + '\n')

    return {
        'chapter_count': len(chapters),
        'chapters_qa_json': str(qa_json_path),
        'qa_txt_path': str(qa_txt_path),
        'warnings': warnings,
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Assemble QA chapters into chapters_qa.json + _qa.txt')
    p.add_argument('--input', required=True,
                   help='Original novel file path (used to derive output stem + dir)')
    p.add_argument('--work-dir', default=None,
                   help='Dir containing qa-chapter-*.md (default: <input-dir>/.work)')
    args = p.parse_args()

    input_path = Path(args.input)
    work_dir = Path(args.work_dir) if args.work_dir else input_path.parent / '.work'

    try:
        summary = assemble(input_path, work_dir)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
