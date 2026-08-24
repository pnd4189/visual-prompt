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
import difflib
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
# Raised from 0.85 once four runs had been measured: healthy chapters land at
# 98.3-100%, while the one that rewrote its prose came in at 91.5% and 87.5% and
# sailed through (observed 2026-08-15). 0.95 keeps three points of headroom under
# the tightest healthy chapter on record.
MIN_QA_CHAPTER_WORD_RETENTION = 0.95

# Aggregate retention cannot see a paragraph being rewritten short: one chapter
# scored a perfect 100% while a single paragraph lost 212 of its 271 words — the
# whole comic riff in it — because other paragraphs had grown. Proofreading
# smooths a sentence; it does not cut a third of one. Paragraphs under this many
# words are skipped, where one clause is a large share of the total.
MIN_QA_PARAGRAPH_RETENTION = 0.70
PARAGRAPH_MEASURE_FLOOR = 12

# A chapter can also stop a few paragraphs early without losing enough words to
# trip either ratio: chapter 383 kept 96% of its words yet dropped the closing
# reveal, and the model wrote a fabricated line over the seam so the text still
# read as finished. So the last source paragraph has to survive somewhere in the
# last few QA paragraphs. Measured on this run: healthy chapters scored 0.97-1.00,
# the two truncated ones 0.27 and 0.31.
MIN_QA_ENDING_COVERAGE = 0.6

_TOKEN_RE = re.compile(r'\w+', re.UNICODE)

# House style softens exactly two words and leaves the rest of the swearing alone:
# "đéo"/"đách" become "éo", while "đếch", "chó nó" and the like stay (decided
# 2026-08-12 — blanket softening drains the voice these novels are read for). The
# QA prompt asks for it, and one run shipped 34 + 7 of them untouched, so the
# assembler applies it too rather than trusting the step to have done it.
_SOFTENED_SLANG_RE = re.compile(r'(?<!\w)[Đđ](?:éo|ách)(?!\w)')

# Translating leftover Chinese is the QA step's first job, and nothing downstream
# ever looked: the later gates all read the scene prompts, never the prose that
# becomes the audio. A proofread that quietly did nothing scores a perfect 100%
# on the retention gate above, so that one cannot catch it either.
_CJK_RE = re.compile(r'[\u4e00-\u9fff]')

# These chapters become YouTube audio, and check_content_safety.py only ever
# reads the scene prompts \u2014 nothing looked at the prose itself. Chapter 37 of
# \u0110\u1ea1o S\u0129 named a child sex offence in a victim's own dialogue and passed every
# gate (observed 2026-08-24). Naming a sexual act alongside a minor is the one
# policy breach that deletes a channel outright, with no strike and no appeal,
# so it is refused rather than warned about.
#
# Both halves must land in the SAME sentence: these novels are full of children
# in ordinary scenes and of adult swearing, and either alone is fine. Requiring
# the pair keeps the gate quiet on both.
_MINOR_RE = re.compile(
    r'(?:tr\u1ebb em|tr\u1ebb nh\u1ecf|tr\u1ebb con|tr\u1ebb g\u00e1i|tr\u1ebb ranh|v\u1ecb th\u00e0nh ni\u00ean|b\u00e9 g\u00e1i|b\u00e9 trai'
    r'|em b\u00e9|\u0111\u1ee9a tr\u1ebb|\u0111\u1ee9a b\u00e9|nh\u1ecf tu\u1ed5i|h\u1ecdc sinh|thi\u1ebfu n\u1eef|thi\u1ebfu ni\u00ean|t\u1ee5i con'
    r'|th\u1eb1ng nh\u1ecf|con nh\u1ecf|t\u1ee5i nh\u1ecf|b\u1ecdn nh\u1ecf|tr\u1ebb v\u1ecb th\u00e0nh ni\u00ean|ch\u01b0a th\u00e0nh ni\u00ean)',
    re.IGNORECASE)
_SEXUAL_RE = re.compile(
    r'(?:giao c\u1ea5u|b\u00e1n d\u00e2m|m\u1ea1i d\u00e2m|d\u00e2m \u0111\u00e3ng|d\u00e2m d\u1eadt|d\u00e2m t\u1eb7c|b\u1ea1o d\u00e2m'
    r'|khi\u00eau d\u00e2m|d\u00e2m \u00f4|l\u00e0m \u0111i\u1ebfm|\u0111i\u1ebfm|g\u00e1i g\u1ecdi|hi\u1ebfp d\u00e2m|c\u01b0\u1ee1ng hi\u1ebfp|x\u00e2m h\u1ea1i t\u00ecnh d\u1ee5c'
    r'|x\u00e2m h\u1ea1i|s\u00e0m s\u1ee1|quan h\u1ec7 t\u00ecnh d\u1ee5c|l\u00e0m t\u00ecnh|th\u1ee7 d\u00e2m|lo\u1ea1n lu\u00e2n|18\+|sex'
    # Abuse and trafficking of a child fall under the same policy, and the
    # register these novels use for ordinary violence ("ch\u00e9m", "\u0111\u00e1nh", "gi\u1ebft")
    # is nowhere near these words \u2014 none of the fifteen chapters measured on
    # 2026-08-24 paired one with a child.
    r'|tra t\u1ea5n|h\u00e0nh h\u1ea1|b\u1ea1o h\u00e0nh|ng\u01b0\u1ee3c \u0111\u00e3i|\u0111\u00e1nh \u0111\u1eadp|b\u00f3c l\u1ed9t|bu\u00f4n ng\u01b0\u1eddi|bu\u00f4n b\u00e1n'
    r'|d\u1ee5 d\u1ed7|x\u00e2m ph\u1ea1m)',
    re.IGNORECASE)
# A few terms are about a minor on their own \u2014 no second word needed.
_CSAE_STANDALONE_RE = re.compile(
    r'(?:\u1ea5u d\u00e2m|khi\u00eau d\u00e2m tr\u1ebb em|m\u1ea1i d\u00e2m tr\u1ebb em|t\u00ecnh d\u1ee5c tr\u1ebb em)', re.IGNORECASE)
# Sentence split is deliberately coarse; a newline ends a sentence too, so a
# minor named in one paragraph cannot pair with a word in the next.
_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?\u2026:;])\s+|\n+')

# One run turned "combat" into "chi\u1ebfn \u0111\u1ea5u", "c\u1edbm" into "c\u00f4ng an", "phake" into
# "nh\u00e1i" and "toang" into "nguy hi\u1ec3m" across three chapters \u2014 every substitution
# one word for one word, so the retention ratios above all read 100% and waved
# it through (observed 2026-08-24). These are the markers of the register these
# novels are read for: internet slang, loanwords and playful coinages, and a
# comic novel rewritten in a serious register is a worse translation, not a
# tidier one.
#
# Reported, never refused (decided 2026-08-24): the list below is fixed while
# every novel coins its own slang, so a hard block would fail whole runs over a
# word this list happens to know \u2014 and worse, it would push the model to leave a
# clumsy machine-translated sentence alone rather than risk rewriting a marker
# out of it. The prompt asks for the register; this counts what actually
# survived so a sweep is visible. Counted per chapter against the source,
# because a word the author never used cannot go missing.
_VOICE_MARKERS = (
    'combat', 'skill', 'check', 'phake', 'auth', 'plot', 'idol', 'cmnr', 'cmn',
    'cmnl', 'toang', 'c\u1edbm', 'o\u00e1nh', 't\u1ea9n', 'ph\u1ed1t', 'h\u00f3ng', 'ch\u00e9m gi\u00f3', 'r\u00e9n',
    'x\u1ecbn s\u00f2', 'c\u00f9i b\u1eafp', 'b\u00e1 \u0111\u1ea1o', 'qu\u1ea9y', 'tr\u1ea9u', 'gato', 's\u1eedu nhi', 'k\u00e8o',
    'tr\u00e0 xanh', 'flex', 'nghi\u1ec7n', 'quay xe', 'b\u00f3c ph\u1ed1t', 'h\u1ea1t g\u1ea1o', 'v\u00e3i',
)
# A few markers are also ordinary words in a wuxia register, so they carry the
# word that must NOT follow: "phốt pho" is the element, "phốt" alone is gossip.
_VOICE_MARKER_EXCLUSIONS = {'phốt': ('pho',), 'kèo': ('nèo',)}
_VOICE_MARKER_RES = tuple(
    (marker, re.compile(
        rf'(?<!\w){re.escape(marker)}(?!\w)'
        + (rf'(?!\s+(?:{"|".join(_VOICE_MARKER_EXCLUSIONS[marker])})(?!\w))'
           if marker in _VOICE_MARKER_EXCLUSIONS else ''),
        re.IGNORECASE))
    for marker in _VOICE_MARKERS)
# One or two may legitimately dissolve when a clumsy machine-translated sentence
# is rewritten whole. Three or more gone from one chapter reads as a sweep and
# is worth a look, which is all this number decides — nothing is refused over it.
MAX_VOICE_MARKERS_LOST = 2

# Quiet self-censorship is invisible to every ratio above: blurring a child sex
# offence out of chapter 37 cost 35 words of 16,545, so the chapter scored 99.8%
# and passed (observed 2026-08-24). It reads as a kindness and sometimes is the
# right call — but the QA step is not the place to decide it silently, because
# nobody downstream can tell a softened line from a faithful one. Deciding what
# ships is the operator's call, so the deletion is surfaced instead of allowed.
# Only flagged when the word vanishes entirely: softening one of four uses is
# ordinary editing, dropping the last one is a decision.
_SENSITIVE_TERMS = (
    'giao cấu', 'bán dâm', 'mại dâm', 'ấu dâm', 'dâm đãng', 'dâm dật', 'dâm tặc',
    'bạo dâm', 'khiêu dâm', 'làm điếm', 'điếm', 'hiếp dâm', 'cưỡng hiếp',
    'xâm hại', 'sàm sỡ', 'loạn luân', 'thủ dâm', 'tự tử', 'tự sát', 'ma túy',
    'heroin', 'cần sa', 'mại độc', 'chích choác',
)
_SENSITIVE_RES = tuple(
    (term, re.compile(rf'(?<!\w){re.escape(term)}(?!\w)', re.IGNORECASE))
    for term in _SENSITIVE_TERMS)


def _soften_slang(text: str) -> tuple[str, int]:
    """House slang rule; returns the rewritten text and how many words changed."""
    return _SOFTENED_SLANG_RE.subn(
        lambda m: 'Éo' if m.group(0)[0] == 'Đ' else 'éo', text)


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


def _compressed_paragraphs(source_text: str, qa_text: str) -> list[tuple[int, int]]:
    """(source words, qa words) for paragraphs the proofread cut short."""
    src, qa = _paragraphs(source_text), _paragraphs(qa_text)
    matcher = difflib.SequenceMatcher(None, [p[:35] for p in src], [p[:35] for p in qa])
    shrunk = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            continue
        for before, after in zip(src[i1:i2], qa[j1:j2]):
            source_words, qa_words = _word_count(before), _word_count(after)
            if source_words < PARAGRAPH_MEASURE_FLOOR:
                continue
            if qa_words < source_words * MIN_QA_PARAGRAPH_RETENTION:
                shrunk.append((source_words, qa_words))
    return shrunk


def _csae_sentences(text: str) -> list[str]:
    """Sentences naming abuse of a minor — the CSAE red line."""
    hits = []
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        if not sentence.strip():
            continue
        if _CSAE_STANDALONE_RE.search(sentence) or (
                _MINOR_RE.search(sentence) and _SEXUAL_RE.search(sentence)):
            hits.append(' '.join(sentence.split())[:160])
    return hits


def _voice_markers_lost(source_text: str, qa_text: str) -> list[str]:
    """Slang words the source used that the proofread no longer has."""
    lost = []
    for marker, pattern in _VOICE_MARKER_RES:
        before = len(pattern.findall(source_text))
        if not before:
            continue
        after = len(pattern.findall(qa_text))
        if after < before:
            lost.append(f'{marker} {before}→{after}')
    return lost


def _sensitive_terms_dropped(source_text: str, qa_text: str) -> list[str]:
    """Sensitive words the source used that the proofread removed completely."""
    dropped = []
    for term, pattern in _SENSITIVE_RES:
        if pattern.search(source_text) and not pattern.search(qa_text):
            dropped.append(term)
    return dropped


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
    slang_softened = 0

    for qp in qa_paths:
        ch = parse_qa_chapter(qp)
        if ch['id'] in seen_ids:
            warnings.append(f"duplicate chapter id {ch['id']} in {qp.name} — kept both")
        seen_ids.add(ch['id'])
        if not ch['text']:
            warnings.append(f"{qp.name} has empty body after frontmatter")
        text, softened = _soften_slang(ch['text'])
        slang_softened += softened
        chapters.append({'id': ch['id'], 'title': ch['title'], 'text': text})
        txt_parts.append(f"{_render_heading(ch['title'])}\n\n{text}")

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
    untranslated = [
        (chapter['id'], ''.join(_CJK_RE.findall(chapter['text'])[:8]))
        for chapter in chapters if _CJK_RE.search(chapter['text'])
    ]
    if untranslated:
        detail = '; '.join(f'{cid}: {sample}' for cid, sample in untranslated)
        raise RuntimeError(
            f'QA left Chinese characters in {len(untranslated)} chapter(s) ({detail}). '
            f'Translating them is STEP 1 of the QA prompt, and no later gate reads '
            f'this text. Fix those chapters and assemble again.'
        )

    flagged = [(chapter['id'], hit)
               for chapter in chapters
               for hit in _csae_sentences(chapter['text'])]
    if flagged:
        detail = '; '.join(f'{cid}: "{hit}"' for cid, hit in flagged[:4])
        raise RuntimeError(
            f'{len(flagged)} sentence(s) name a sexual act alongside a minor '
            f'({detail}). YouTube deletes a channel for this with no strike and '
            f'no appeal, and no other gate reads this prose. Keep what happens in '
            f'the story — the victims, the crime, the consequences — but do not '
            f'name the act: say "phạm tội" rather than the offence, "chuyện hư '
            f'hỏng" rather than the trade. Then assemble again.'
        )

    # chapters.json is the proof that STEP 1 read the file the user named. Without
    # it every measurement below compares the proofread against itself: one run
    # skipped load and continuity outright, wrote ten chapters of a different novel
    # from memory, and sailed through — the per-chapter check had quietly stepped
    # aside, and the total happened to land within 6% of the real word count
    # (observed 2026-08-13). Refuse instead of degrading.
    source_texts = _source_chapters(work_dir)
    if not source_texts:
        raise RuntimeError(
            'no readable .work/chapters.json, so there is nothing to check this '
            'proofread against. Run STEP 1 (load_input.py) on the input file first; '
            'a QA pass with no source behind it cannot be verified at all.'
        )
    qa_ids, source_ids = {c['id'] for c in chapters}, set(source_texts)
    if qa_ids != source_ids:
        extra, missing = sorted(qa_ids - source_ids), sorted(source_ids - qa_ids)
        raise RuntimeError(
            f'the proofread chapters are not the ones that were loaded — '
            f'{len(extra)} not in chapters.json ({extra[:5]}), '
            f'{len(missing)} loaded but never proofread ({missing[:5]}). '
            f'The QA step must work through .work/chapters.json, not from memory.'
        )
    if source_texts:
        gutted, truncated, compressed = [], [], []
        for chapter in chapters:
            source_text = source_texts.get(chapter['id'])
            if source_text is None:
                continue
            kept, src_words = _word_count(chapter['text']), _word_count(source_text)
            if kept < src_words * MIN_QA_CHAPTER_WORD_RETENTION:
                gutted.append(f"{chapter['id']} kept {kept}/{src_words} words")
            elif _ending_coverage(source_text, chapter['text']) < MIN_QA_ENDING_COVERAGE:
                truncated.append(str(chapter['id']))
            else:
                shrunk = _compressed_paragraphs(source_text, chapter['text'])
                if shrunk:
                    worst = min(shrunk, key=lambda pair: pair[1] / pair[0])
                    compressed.append(
                        f"{chapter['id']}: {len(shrunk)} paragraph(s), worst "
                        f"{worst[1]}/{worst[0]} words")
            # Both of these warn rather than refuse. Softening a sensitive word
            # is sometimes the right call for a YouTube upload, and slang moves
            # around legitimately when a clumsy sentence is rewritten; neither is
            # worth failing a run over. They just have to be visible.
            lost = _voice_markers_lost(source_text, chapter['text'])
            if len(lost) > MAX_VOICE_MARKERS_LOST:
                warnings.append(
                    f"chapter {chapter['id']}: slang written out — "
                    f"{', '.join(lost[:6])}. That register is the voice; check "
                    f"this was a rewrite, not a sweep to standard prose")
            dropped = _sensitive_terms_dropped(source_text, chapter['text'])
            if dropped:
                warnings.append(
                    f"chapter {chapter['id']}: QA removed {', '.join(dropped[:6])} "
                    f"— check this was meant, not a silent softening")
        if gutted or truncated or compressed:
            detail = '; '.join(
                part for part in (
                    f"short chapters: {', '.join(gutted)}" if gutted else '',
                    f"chapters missing their ending: {', '.join(truncated)}" if truncated else '',
                    f"paragraphs rewritten short: {'; '.join(compressed)}" if compressed else '',
                ) if part
            )
            raise RuntimeError(
                f'QA dropped text inside '
                f'{len(gutted) + len(truncated) + len(compressed)} chapter(s) '
                f'({detail}). Proofreading does not shorten the story. Re-run the QA '
                f'loop for those chapters before assembling.'
            )

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
        'slang_softened': slang_softened,
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
