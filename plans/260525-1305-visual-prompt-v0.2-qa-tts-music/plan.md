---
title: "Visual Prompt v0.2 — QA Gate + TTS File + Lyria Music Prompts"
description: "Add QA proofread gate (auto-fix residual CJK/EN + grammar, output TTS-ready story) and Lyria instrumental music prompt output to the visual-prompt pipeline"
status: implemented
priority: P2
branch: "main"
tags: [skill, antigravity, llm-driven, qa, tts, lyria, music]
blockedBy: []
blocks: []
created: "2026-05-25T06:07:52.630Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt v0.2 — QA Gate + TTS File + Lyria Music Prompts

## Overview

Extend the `/visual-prompt` pipeline (v0.1 = `260522-2230-...`, status implemented)
with three additions, all driven from one QA'd source of truth:

1. **QA proofread gate** (new STEP 1.5) — LLM auto-fixes residual Chinese/English
   characters, spelling/grammar, clunky MT sentences; splits over-long sentences.
   Moderate edits only (no plot change). Always runs, resume-safe per chapter.
2. **TTS file** — the QA'd story `<stem>_qa.txt` doubles as the TTS-ready input for
   TTS_Local (VieNeu + VietVoice). No separate artifact (verified: both engines split
   on punctuation only). Chapter titles kept + terminal period for pause.
3. **Lyria music prompts** (new STEP 6.5) — analyze story emotional arc → 3-5 mood
   regions (default 4, `--music N` override) → one English instrumental Lyria prompt
   per region with vocal-exclusion negatives. Output `<stem>_music_prompts.txt`.

All downstream steps (bible/genre/scene) now read the QA'd text. Architecture
unchanged: LLM-driven loop, Python = I/O only. No code copied from Grammar_check
or TTS_Local.

Output set grows from 2 → 4 files next to input:
`_qa.txt` ★, `_image_prompts.txt`, `_video_prompts.txt`, `_music_prompts.txt` ★.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [QA Proofread Gate](./phase-01-qa-proofread-gate.md) | Done |
| 2 | [Lyria Music Prompts](./phase-02-lyria-music-prompts.md) | Done |
| 3 | [Docs and End-to-End Test](./phase-03-docs-and-end-to-end-test.md) | Done (scripts E2E; full LLM run pending in Antigravity) |

Build order: 1 → 2 → 3 (Phase 2 reads `chapters_qa.json` from Phase 1; Phase 3
documents + tests the full chain).

## Key Dependencies

- Brainstorm source: `plans/reports/brainstorm-260525-1305-visual-prompt-v0.2-qa-tts-music.md`
- Builds on v0.1 plan `260522-2230-visual-prompt-skill-implementation` (implemented).
- Reference projects (read-only, DO NOT copy): `/home/dung/VIBE_CODING/Grammar_check`,
  `/home/dung/VIBE_CODING/TTS_Local`. tran-qa skill: `~/.gemini/skills/tran-qa/SKILL.md`.

## Dependencies

No cross-plan blockers — v0.1 is complete.

## Validation Log

Date: 2026-05-25 · Mode: `/ck:plan validate`

**Verification Pass (Standard tier — Fact Checker + Contract Verifier):** All claimed
touchpoints verified against the live codebase, no errors:
- `scripts/_io_utils.py` — `atomic_write_json` (L11) + `atomic_write_text` (L34) exist.
- `scripts/calc_scene_count.py` — `--chapters-json` flag exists (L57), reads JSON (L66-67).
- `scripts/assemble_outputs.py` — `_FRONTMATTER_RE` (L35), `discover_scenes()` (L43),
  `parse_scene()` (L47), `assemble()` (L60), `--input`/`--work-dir`, JSON summary (L119).
  Phase 2's `discover_music()`/`parse_music()` mirror this pattern cleanly.
- `commands/visual-prompt.toml` — STEP 0 flag parse (L11), STEP 1→`chapters.json` (L40),
  STEP 4 `--chapters-json` (L88), STEP 5 key `sha1(input_hash+bible_hash+images_n+videos_m)`
  (L101), STEP 6 key `sha1(input_hash+bible_hash+plan_hash+serialize(scene_row))` (L123),
  force-redo `rm -f .work/scene-*.md` (L117), POST-RUN SUMMARY (L166). Phase 1's
  `input_hash`→`qa_hash` re-point matches the real formulas.

**Critical questions resolved:**
1. **`--music N` out-of-[3,5] behavior** → **Honor verbatim, no clamp.** `--music 8` → 8
   regions, `--music 1` → 1. The [3,5] clamp applies ONLY to the adaptive (no-flag) path.
   Propagated to phase-02 (Requirements, STEP 6.5, Impl Step 2, Success Criteria).
2. **Genre pre-gate before QA?** → **No.** Keep QA → genre order. QA must infer
   translation context FROM THE FILE ITSELF, genre-agnostic, no hard-gating by genre
   ("không cần gò bó cố định"). Propagated to phase-01 (Requirements fix list).
   Note (out of v0.2 scope, not changed): v0.1 genre refusal of đam mỹ/ngôn tình at
   STEP 3 remains as-is; user's instruction scoped to QA translation behavior.
