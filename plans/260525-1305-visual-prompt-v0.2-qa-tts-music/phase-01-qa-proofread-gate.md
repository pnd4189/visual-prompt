---
phase: 1
title: "QA Proofread Gate"
status: done
priority: P1
effort: "4-6h"
dependencies: []
---

# Phase 1: QA Proofread Gate

## Overview

Insert STEP 1.5 between Load (STEP 1) and Bible (STEP 2): an LLM proofread pass
that fixes residual Chinese/English characters, spelling/grammar, and clunky
machine-translation sentences (moderate level — no plot change), then writes a
QA'd source of truth `chapters_qa.json` + a TTS-ready `<stem>_qa.txt`. All
downstream steps (bible/genre/scene-count/scene-plan/expand) re-point to the
QA'd text. The `_qa.txt` file IS the TTS input for VieNeu + VietVoice.

## Requirements

- **Functional**
  - QA always runs (no skip flag in v0.2). Resume-safe per chapter via SHA1 cache.
  - Fix: residual CJK / pinyin / untranslated English → translate by inferring the
    surrounding context FROM THE FILE ITSELF (genre-agnostic; QA runs before
    genre-detect, so it must not depend on or hard-gate by genre); spelling, grammar,
    punctuation; rewrite clunky MT sentences for fluency; split sentences > ~200
    chars (VieNeu chunk-safety).
  - FORBIDDEN: add/remove plot, change proper nouns, change numbers/quantities,
    change tone/voice of the author. Moderate edits only.
  - Output `chapters_qa.json` (same schema `{id,title,text}` as `chapters.json`)
    consumed by all downstream steps.
  - Output `<stem>_qa.txt`: human-readable + TTS-ready. Chapter heading rendered
    as `Chương N: Title.` (terminal period so TTS pauses; `clean_text()` strips
    newlines). Numbers kept as-is. Prose paragraphs preserved.
- **Non-functional**
  - LLM-driven; Python = I/O only. No deps beyond stdlib (+ existing python-docx).
  - No code copied from Grammar_check.

## Architecture

Data flow:
```
chapters.json ──(per-chapter LLM QA)──> .work/qa-chapter-NNN.md
                                              │ (frontmatter cache_key)
                                              ▼
                          scripts/assemble_qa.py
                                              │
                        ┌─────────────────────┴───────────────────┐
                        ▼                                          ▼
              .work/chapters_qa.json                     <input_dir>/<stem>_qa.txt
              (downstream source)                        (TTS file, human-readable)
```

Cache keys:
- Per-chapter: `cache_key = sha1(input_hash + serialize(chapter_row))[:16]`.
- `qa_hash = sha1(file_bytes(chapters_qa.json))[:12]` → written to `.work/qa.hash`.
- Downstream cache keys (STEP 5 plan, STEP 6 scene) **replace `input_hash` with
  `qa_hash`** because they now consume QA'd text. STEP 5: `sha1(qa_hash + bible_hash
  + images_n + videos_m)`; STEP 6: `sha1(qa_hash + bible_hash + plan_hash + scene_row)`.
- Bible extraction/augmentation (STEP 2) and genre (STEP 3) read `chapters_qa.json`.
- `--force-redo` deletes `qa-chapter-*.md` BEFORE the QA loop (in addition to
  existing `scene-*.md` cleanup).

Over-long single chapter (no `Chương` markers → 1 huge chapter): the QA prompt
must internally process the chapter in sequential prose segments and concatenate,
preserving order. Document the segment threshold in the prompt (~3000 words/segment).

## Related Code Files

- Create: `prompts/qa-proofread.md` — LLM QA instructions (VN), moderate level,
  explicit forbidden list + concrete fix examples (CJK residue, pinyin, clunky MT,
  long-sentence split). Output contract: write `.work/qa-chapter-NNN.md` with
  frontmatter `{chapter_id, cache_key}` + body = corrected chapter text.
- Create: `scripts/assemble_qa.py` — read `.work/qa-chapter-*.md` (sorted by id),
  rebuild `chapters_qa.json` (schema `{id,title,text}`) + write `<stem>_qa.txt`
  (chapter heading `Chương N: Title.`, blank line, body). Use `atomic_write_json`
  + `atomic_write_text` from `_io_utils`. Mirror the parse pattern of
  `assemble_outputs.py` (frontmatter regex + body extraction).
- Modify: `commands/visual-prompt.toml` — insert STEP 1.5 (QA loop, resume-safe,
  same structure as STEP 6 expand loop); thread `qa_hash`; re-point STEP 2/3/4/5/6
  source from `chapters.json` → `chapters_qa.json`; extend `--force-redo` cleanup;
  update STEP 5/6 cache-key formulas (`input_hash` → `qa_hash`); add `_qa.txt` to
  the POST-RUN SUMMARY with a "Đưa vào TTS_Local" hint line.
- Modify: `scripts/calc_scene_count.py` — STEP 4 call passes
  `--chapters-json .work/chapters_qa.json` (script already supports the flag; only
  the toml call site changes, so wordcount derives from QA'd text).

## Implementation Steps

1. Write `prompts/qa-proofread.md`: ROLE (editor), INPUT (one chapter row from
   `chapters_qa` loop), TASK (fix list), FORBIDDEN list, long-sentence split rule
   (>200 chars), segment-large-chapter rule, OUTPUT contract (qa-chapter-NNN.md +
   frontmatter). Include 3-4 concrete before/after examples in Vietnamese.
2. Write `scripts/assemble_qa.py` (argparse `--input`, optional `--work-dir`,
   default `<input-dir>/.work`). Discover `qa-chapter-*.md`, parse frontmatter +
   body, sort by chapter id, write `chapters_qa.json` + `<stem>_qa.txt`. Print JSON
   summary (chapter_count, qa_txt_path, warnings for missing chapters). Exit 1 if
   no qa-chapter files found.
3. Edit `commands/visual-prompt.toml`:
   - STEP 0: (no new flag here — `--music` belongs to Phase 2).
   - Insert **STEP 1.5 — QA PROOFREAD**: load `chapters.json`; loop chapters
     1..K; per chapter compute cache_key, skip if cached & not `--force-redo`,
     else load `@prompts/qa-proofread.md` + execute → `.work/qa-chapter-NNN.md`;
     after loop run `python3 scripts/assemble_qa.py --input "<input_path>"`;
     compute `qa_hash` → `.work/qa.hash`.
   - Re-point STEP 2 (bible), STEP 3 (genre), STEP 4 (calc), STEP 5 (plan),
     STEP 6 (expand) to read `.work/chapters_qa.json`.
   - Update STEP 5 + STEP 6 cache-key formulas: `input_hash` → `qa_hash`.
   - STEP 6 `--force-redo`: also `rm -f .work/qa-chapter-*.md` at the QA loop entry.
   - POST-RUN SUMMARY: add `📝 <stem>_qa.txt` line + TTS usage hint.
4. Manual dry check: confirm regex/paths in `assemble_qa.py` compile
   (`python3 -c "import ast; ast.parse(open('scripts/assemble_qa.py').read())"`)
   and `python3 scripts/assemble_qa.py --help` runs.

## Success Criteria

- [ ] `prompts/qa-proofread.md` exists with forbidden list + ≥3 concrete examples.
- [ ] `scripts/assemble_qa.py` compiles, `--help` works, exits 1 cleanly when no
      qa-chapter files present.
- [ ] Given fake `.work/qa-chapter-001.md` + `-002.md`, `assemble_qa.py` produces
      valid `chapters_qa.json` (schema match) + `<stem>_qa.txt` with
      `Chương N: ....` headings ending in a period.
- [ ] `commands/visual-prompt.toml` STEP 1.5 present; STEP 2-6 read
      `chapters_qa.json`; STEP 5/6 cache keys use `qa_hash`; `--force-redo` clears
      `qa-chapter-*.md`; summary lists `_qa.txt`.
- [ ] No code copied from Grammar_check (originality check).

## Risk Assessment

- **Over-aggressive QA changes meaning.** Mitigation: explicit FORBIDDEN list +
  before/after examples in the prompt; moderate-level wording; preserve proper
  nouns/numbers.
- **Huge single-chapter input** blows LLM context. Mitigation: segment rule in
  prompt; resume-safe so a crash mid-chapter can re-run.
- **Cache-key migration bug** (downstream not regenerating after QA). Mitigation:
  test that changing input → new `qa_hash` → stale warning + regenerate path fires.
- **`clean_text()` merges chapter title into first sentence** if no terminal punct.
  Mitigation: assemble_qa.py forces `Chương N: Title.` with trailing period.
