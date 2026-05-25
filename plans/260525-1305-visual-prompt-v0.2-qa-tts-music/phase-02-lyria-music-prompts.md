---
phase: 2
title: "Lyria Music Prompts"
status: done
priority: P2
effort: "4-5h"
dependencies: [1]
---

# Phase 2: Lyria Music Prompts

## Overview

Insert STEP 6.5 (after Expand): analyze the story's emotional arc, segment it into
3-5 adjacent mood regions (default 4, `--music N` override), and emit one detailed
English instrumental Lyria prompt per region into `<stem>_music_prompts.txt`. Each
prompt targets Lyria 3 in the Gemini app (paste text), is instrument-only with
explicit vocal-exclusion negatives, ~2-3 min seamless loop. Reuses genre detection
+ scene-plan emotional beats — no re-analysis from scratch.

## Requirements

- **Functional**
  - Parse `--music N` (positive int) in STEP 0. When given, **honor N exactly** —
    no clamp (user is authoritative; `--music 8` → 8 regions, `--music 1` → 1).
  - Adaptive segmentation (only when `--music` NOT given): group consecutive
    scenes/chapters into mood regions; clamp to [3,5]; default 4. The clamp applies
    to the adaptive path ONLY, never to an explicit `--music N`.
  - Per region → one Lyria prompt using the DeepMind template:
    `[Genre & style] + [Mood] + [Instrumentation] + [Tempo/BPM + key] + "Instrumental."`
    plus a negative line `no vocals, no lyrics, no singing, no spoken word` and a
    `seamless loop, no fade out` cue.
  - Prompt **body in English** (Lyria works best in English); navigation **label in
    Vietnamese**: `--- LOOP i / N — Chương X-Y — mood: <vn> ---`.
  - Instrument palette culturally matched via genre (e.g., tiên hiệp/võ hiệp →
    guzheng, dizi, erhu, pipa, ambient pads; tension → taiko + low strings).
  - Output `<stem>_music_prompts.txt` next to input.
- **Non-functional**
  - LLM-driven; Python = I/O only. Resume-safe per region.
  - No code copied from TTS_Local / Grammar_check.

## Architecture

Data flow:
```
chapters_qa.json + genre + .work/scene-plan.md
        │ (LLM mood-arc segmentation → N regions; N = --music if given, else adaptive 3-5)
        ▼
.work/music-NNN.md  (frontmatter cache_key + body = full Lyria prompt block)
        │
        ▼ scripts/assemble_outputs.py  (extended)
<input_dir>/<stem>_music_prompts.txt
```

Cache key per region: `cache_key = sha1(qa_hash + genre + plan_hash + region_spec)[:16]`
where `region_spec` = serialized `{loop_index, total, chapter_start, chapter_end,
mood}`. `--force-redo` deletes `music-*.md`.

`assemble_outputs.py` extension: add `discover_music()` (glob `music-*.md`) + a
`_MUSIC_RE`-free plain-body parse (the whole body after frontmatter is the prompt
block) → write `<stem>_music_prompts.txt`. Keep image/video assembly unchanged.
Extend the printed JSON summary with `music_count` + `music_path`.

Segmentation guidance lives in `references/music-mood-mapping.md` (genre × emotion →
instruments / BPM range / key / descriptors), mirroring the existing `references/`
pattern (e.g. `genre-keywords.md`).

## Related Code Files

- Create: `prompts/music-prompt-builder.md` — ROLE (film-score music director),
  INPUT (`chapters_qa.json`, genre, `scene-plan.md`, `--music N`), TASK
  (segment arc → N regions: N = `--music` verbatim if given, else adaptive clamp 3-5;
  per region build Lyria prompt via
  `@references/music-mood-mapping.md`), OUTPUT contract (`.work/music-NNN.md` with
  frontmatter + body), hard rule INSTRUMENTAL ONLY + negative line. 1-2 full
  example blocks.
- Create: `references/music-mood-mapping.md` — table: per supported genre
  (tien-hiep, huyen-huyen, do-thi, co-dien, vo-hiep) × mood bucket (calm/intro,
  mystery/journey, tension/battle, sad/reflection, triumph/resolution) →
  instrument palette, BPM range, suggested key/scale, English mood descriptors.
- Modify: `commands/visual-prompt.toml` —
  - STEP 0: add `--music (\\d+)` → `music_override`; update flag echo + unknown-flag
    error string.
  - Insert **STEP 6.5 — MUSIC PROMPTS** after STEP 6: resolve count (if `--music N`
    given → use N verbatim; else adaptive default 4, clamp 3-5); loop regions; per
    region cache-check then load
    `@prompts/music-prompt-builder.md` → `.work/music-NNN.md`; `--force-redo` clears
    `music-*.md`.
  - POST-RUN SUMMARY: add `🎵 <stem>_music_prompts.txt — <N> loop` line + Lyria hint.
- Modify: `scripts/assemble_outputs.py` — add music discovery + write
  `<stem>_music_prompts.txt`; extend summary JSON. STEP 7 call unchanged (same
  `--input`), so the assembler picks up music files automatically.

## Implementation Steps

1. Write `references/music-mood-mapping.md` (the knowledge table). Verify instrument
   names are valid English Lyria descriptors.
2. Write `prompts/music-prompt-builder.md` with the segmentation algorithm
   (consecutive grouping; adaptive path clamps 3-5; explicit `--music N` honored
   verbatim, no clamp), the Lyria template, the
   INSTRUMENTAL-ONLY hard rule + negative line, and 1-2 example blocks.
3. Edit `commands/visual-prompt.toml`: add `--music` to STEP 0 parse/echo; insert
   STEP 6.5; extend `--force-redo` + summary.
4. Edit `scripts/assemble_outputs.py`: add `discover_music()` + `parse_music()`
   (body = everything after frontmatter), write `_music_prompts.txt`, extend
   summary JSON with `music_count` + `music_path`.
5. Dry check: `python3 -c "import ast; ast.parse(open('scripts/assemble_outputs.py').read())"`;
   with fake `music-001.md`/`002.md`, confirm `_music_prompts.txt` assembled in order.

## Success Criteria

- [ ] `references/music-mood-mapping.md` covers all 5 genres × 5 mood buckets.
- [ ] `prompts/music-prompt-builder.md` enforces INSTRUMENTAL ONLY + negative line,
      English body + VN label, adaptive clamp 3-5, explicit `--music N` honored verbatim.
- [ ] `--music 3` → 3 regions; `--music 8` → 8 regions (honored, no clamp);
      `--music 1` → 1 region; no flag → 4 (adaptive within 3-5).
- [ ] `assemble_outputs.py` extended: fake `music-*.md` → ordered
      `<stem>_music_prompts.txt`; image/video assembly unchanged (regression check).
- [ ] Every generated block contains `Instrumental.` + the negative line +
      `seamless loop`.
- [ ] STEP 0 rejects unknown flags still; `--music` accepted.

## Risk Assessment

- **Lyria may still emit vocal-like pads** despite negatives — model limitation,
  documented in HUONG-DAN (Phase 3). Prompt minimizes, can't guarantee.
- **Flat-mood stories** → 3 near-identical loops. Mitigation: allow drop to 3;
  prompt instructs distinct instrumentation/intensity per region.
- **assemble_outputs.py regression** on image/video. Mitigation: keep existing
  functions untouched; add music as a separate code path; regression check in S.C.
- **Region→timeline sync is manual.** Mitigation: label each loop with `Chương X-Y`
  so the user places it correctly; documented in Phase 3.
