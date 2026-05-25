---
phase: 2
title: "Python I/O Scripts"
status: done
priority: P1
effort: "0.5d"
dependencies: [1]
---

# Phase 2: Python I/O Scripts

## Overview

Minimal Python helpers — Gemini Ultra is the loop driver; Python only handles file I/O the LLM can't do safely (chapter parsing with encoding fallback, atomic writes, scene count math, final assembly). 4 scripts total, ~250 LOC, copied/adapted from proven `chinese-novel-proofreader` v3.6.

## Context Links

- Reference scripts: `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/scripts/{load_input.py, _io_utils.py, assemble_outputs.py}`
- Brainstorm §6 (script inventory), §7 (scene count formula)

## Requirements

**Functional:**
- `load_input.py` parses .txt/.md/.docx → JSON chapter list with stable IDs; encoding fallback (utf-8-sig → utf-8 → gbk → gb18030 → cp1252)
- `_io_utils.py` provides `atomic_write_text()` + `atomic_write_json()` (crash-safe via tempfile + os.replace)
- `calc_scene_count.py` computes default `images = round(wordcount / 200)`, `videos = round(images / 7)`; CLI flags override
- `assemble_outputs.py` discovers `.work/scene-NNN.md`, extracts `## Image Prompt` + `## Video Prompt` blocks, emits 2 files: `<input>_image_prompts.txt` + `<input>_video_prompts.txt`

**Non-functional:**
- Pure stdlib + optional `python-docx` (lazy import, only when .docx detected)
- No external state; idempotent
- Each script <200 lines; runnable standalone with `python3 scripts/<name>.py --help`

## Architecture

```
scripts/
├── load_input.py         # COPY from proofreader (zero changes)
├── _io_utils.py          # COPY from proofreader (zero changes)
├── calc_scene_count.py   # NEW — wordcount → (images, videos) with override flags
└── assemble_outputs.py   # ADAPT from proofreader — 2 outputs not 6, scene-NNN.md not *-prompts.md
```

Data flow:
```
input.txt ─→ load_input.py ─→ .work/chapters.json
                                    │
                                    ├─→ calc_scene_count.py ─→ stdout: {"images": N, "videos": M}
                                    │
                                    └─→ (Phase 4 LLM writes .work/scene-001.md ... scene-NNN.md)
                                                    │
                                                    └─→ assemble_outputs.py ─→ input_image_prompts.txt + input_video_prompts.txt
```

## Related Code Files

### Create
- `scripts/load_input.py` — verbatim copy from `chinese-novel-proofreader/scripts/load_input.py` (74 lines, chapter regex + encoding fallback)
- `scripts/_io_utils.py` — verbatim copy from `chinese-novel-proofreader/scripts/_io_utils.py` (50 lines, atomic writes)
- `scripts/calc_scene_count.py` — NEW (~60 lines): CLI `--input <file> [--images N] [--videos M]`; reads `.work/chapters.json` (or raw file as fallback), sums words, prints JSON `{"images": int, "videos": int, "source": "auto|override"}`
- `scripts/assemble_outputs.py` — **NEAR-REWRITE** (~150 lines, NOT verbatim — proofreader's script depends on `format_tts.py` + parses `## Scene N` not `## Image Prompt` and emits 6 outputs not 2): discovers `.work/scene-*.md`, extracts `## Image Prompt` (always present) and `## Video Prompt` (optional per scene), writes 2 .txt files with separators; video output uses original scene index (e.g., `--- SCENE 007 ---` not `--- VIDEO 1 ---`) so gaps are visible and traceable
- `scripts/append_bible_row.py` — NEW (~40 lines, defensive helper for red-team #11): given existing bible path + YAML row, appends row to end without touching existing content; LLM calls this instead of rewriting whole bible (eliminates byte-identity drift risk)

### Modify
- (none)

### Delete
- (none — Phase 1 created empty `scripts/` via .gitignore parent)

## Implementation Steps

1. **Copy `load_input.py` verbatim** from proofreader. Verify chapter regex matches Vietnamese xianxia conventions (`Chương 1: Tên chương`, `CHƯƠNG 1`, etc.). Smoke-test with sample input.
2. **Copy `_io_utils.py` verbatim** from proofreader. No changes — `atomic_write_text(path, content)` and `atomic_write_json(path, obj)` work identically here.
3. **Write `calc_scene_count.py`** (NEW):
   - Argparse: `--input <path>` required; `--images N` optional override; `--videos M` optional override; `--chapters-json <path>` optional (default `.work/chapters.json`)
   - Load chapters JSON if exists, else read raw file with same encoding fallback
   - Compute `wordcount = sum(len(ch['text'].split()) for ch in chapters)`
   - Default: `images = round(wordcount / 200)`, `videos = round(images / 7)`; clamp `images >= 5`, `videos >= 2`
   - Override: if `--images` given use it; if `--videos` given use it; else compute
   - Print JSON to stdout: `{"images": N, "videos": M, "wordcount": W, "source": "auto"|"override"|"mixed"}`
   - Exit 0 on success, 1 on file not found
4. **Rewrite `assemble_outputs.py`** (NOT a verbatim adapt — proofreader's script structurally differs):
   - Argparse: `--input <original-file-path>` (used to derive output filename stem) + `--work-dir <path>` (default `.work/`)
   - Glob `.work/scene-*.md` sorted by filename (zero-padded NNN ensures lexical = numeric order)
   - For each file, parse markdown headers: extract content under `## Image Prompt` (always) and `## Video Prompt` (may be absent)
   - Concatenate image prompts with separator `\n\n--- SCENE NNN ---\n\n` (NNN = scene index from filename, preserves ordering)
   - Concatenate video prompts with same separator using ORIGINAL scene index (gaps visible — Scene 007, Scene 014 — not renumbered 1, 2)
   - Write to `<input-stem>_image_prompts.txt` and `<input-stem>_video_prompts.txt` via `atomic_write_text`
   - Print summary: `Wrote N image prompts + M video prompts (indices: 7, 14, 21, ...) to <output-dir>/`
   - Exit 0 on success, 1 if no scene files found (with clear error message)
   - If a `scene-NNN.md` exists but missing `## Image Prompt` block → log WARNING with filename + skip, don't crash
5. **Write `append_bible_row.py`** (NEW, defensive helper):
   - Argparse: `--bible <path>` + `--row <yaml-row-string>` (single YAML row to append)
   - Validate row is well-formed YAML (use `yaml.safe_load`); reject if not
   - Open bible in append mode; write `\n{row}\n`; flush + fsync
   - Print confirmation: `Appended row to <bible-path> (now N total rows)`
   - Why: red-team #11 — eliminates risk of LLM rewriting whole bible and accidentally editing existing rows
6. **Add `scripts/__init__.py`** (empty) — makes `scripts/` importable for cross-script reuse
7. **Smoke test each script standalone:**
   - `python3 scripts/load_input.py --input sample.txt --output .work/chapters.json`
   - `python3 scripts/calc_scene_count.py --input sample.txt` → prints JSON
   - Create fake `.work/scene-001.md` (image only) + `.work/scene-007.md` (image + video) → `python3 scripts/assemble_outputs.py --input sample.txt` → image .txt has 2 blocks, video .txt has 1 block (indexed as SCENE 007)
   - `python3 scripts/append_bible_row.py --bible /tmp/bible.md --row '- name: Test, age: 20, ...'` → row appended; rerun → 2 rows; existing content byte-identical
   - **Vietnamese path test:** `python3 scripts/load_input.py --input "Đại Đạo Triều Thiên.txt"` — must not crash on diacritics
8. **Verify atomic writes**: kill script mid-write (Ctrl+C), confirm output file is either fully written or absent (no half-written `.tmp` lingering after retry)

## Todo List

- [ ] `scripts/load_input.py` copied + smoke tested
- [ ] `scripts/_io_utils.py` copied
- [ ] `scripts/calc_scene_count.py` written + smoke tested (auto + override paths)
- [ ] `scripts/assemble_outputs.py` adapted + smoke tested with fake scene files
- [ ] `scripts/append_bible_row.py` written + tested (append-only, no edit risk)
- [ ] `scripts/__init__.py` created (empty)
- [ ] Atomic write crash-safety verified manually
- [ ] Vietnamese filename test passes (Đại Đạo Triều Thiên.txt loadable)

## Success Criteria

- [ ] `python3 scripts/load_input.py --input <vietnamese-novel.txt> --output .work/chapters.json` produces valid JSON with `[{id, title, text}, ...]`
- [ ] `python3 scripts/calc_scene_count.py --input <10k-word-file>` returns `images: ~50, videos: ~7` (within ±2 of formula)
- [ ] `python3 scripts/calc_scene_count.py --input <file> --images 12 --videos 5` returns exactly `{"images": 12, "videos": 5, "source": "override"}`
- [ ] `python3 scripts/assemble_outputs.py --input sample.txt` emits 2 .txt files with `--- SCENE NNN ---` separators
- [ ] No `*.tmp` files left in `.work/` after normal or interrupted runs

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Vietnamese filename with diacritics breaks glob | Use `pathlib.Path` everywhere; test with `Đại Đạo Triều Thiên.txt` |
| python-docx missing on user system | Lazy import inside .docx branch only; print install hint if ImportError |
| `.work/scene-NNN.md` malformed (missing `## Image Prompt`) | `assemble_outputs.py` logs WARNING + skips that scene; doesn't crash |
| Wordcount inflated by Chinese chars in mixed text | `len(text.split())` measures whitespace tokens; xianxia files post-proofread are VN, so safe |
| Scene count formula wrong for very short files (<2k words) | Clamp `images >= 5`, `videos >= 2` floors |

## Security Considerations

- All paths user-relative; no shell injection (use `subprocess` only if needed, with list args not string)
- `python-docx` parses local .docx only — no network
- No secret handling in this phase

## Next Steps

- **Unlocks:** Phase 4 (LLM prompt files reference `python3 scripts/<name>.py` commands inside workflow)
- **Verification needed:** Smoke tests above + Phase 5 end-to-end will catch integration issues
