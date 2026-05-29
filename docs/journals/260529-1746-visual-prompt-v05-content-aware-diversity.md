# Visual Prompt v0.5 — Content-Aware Scene Diversity

**Date**: 2026-05-29 17:46
**Severity**: Medium
**Component**: visual-prompt skill — calc/assemble scripts, scene-planner, expanders, toml orchestration
**Status**: Implemented (deterministic parts verified; LLM end-to-end run pending Agy CLI)

## What Happened

v0.4 added strong scene-diversity wording but it was model-honored only, and its
35–45% action target was wrong for talky stories. Verify proved the sample novel
is ~22:1 talk:combat — forcing a combat quota would fabricate plot. v0.5 makes
diversity targets content-aware, draws anti-monotony from VISUAL variety instead
of fake combat, fixes the synopsis-fragment bug, and adds two deterministic gates.

## Decisions

- **Content-aware density (not a global quota).** `calc_scene_count.py` scans
  combat vocab → `action_density` (low <2 / med 2–6 / high >6 hits per 1k words)
  → `recommended_mix` band the planner consumes. The old 35–45% figure is now the
  high-density band only. Sample → `low` (0.73 hits/1k).
- **Anti-monotony = visual variety** (camera/scale, real group tableaus, object
  inserts, flashback, weather) with a hard no-fabrication guard. v0.4 combat vocab
  stays available for stories that genuinely have action.
- **Synopsis fix:** planner emits a coherent one-line sentence; plan gate rejects
  raw text slices (leading-lowercase heuristic, conservative).
- **Two deterministic gates:** plan gate (`validate_scene_plan.py`, new) rejects
  adjacent-duplicate triples + fragment synopses; depth gate (in
  `assemble_outputs.py`) rejects shallow blocks (missing headers / word count /
  <20 negatives / video >3800 chars). Both wired into toml with bounded
  (max-2) revise/regen loops that WARN-and-proceed, never hard-block.
- **Video cap is now characters, not words:** HARD CAP 3800 chars (Veo3/Flow reject
  >4000). Same constant in expander + template + depth gate (DRY).
- **`--epic`** bumps the mix band one notch and favors spectacle; the no-fabrication
  guard still holds above it.
- **Gold example stays single-source** in `visual-prompt-template.md`; the image
  expander references + must match its depth, no duplicated block.
- **One new file only:** `scripts/validate_scene_plan.py`. Density folded into
  calc; depth folded into assemble.

## Verification

Deterministic PASS: all 3 scripts compile; calc emits density (sample low, combat
fixture high, --epic bumps, old keys intact); validate flags 14 fragments + dups
on the real sample (exit 2), clean plan exit 0; depth gate flags shallow/oversize
blocks, rich block clean, `.txt` byte-compatible. Static grep: no unconditional
35–45% default; version synced 0.5.0 in both SKILL.md + gemini-extension.json
(gemini was stale at 0.3.0 — fixed).

## Open / Not Verified

- Full `--force-redo` end-to-end LLM run (~116 scenes) needs the Agy CLI runtime —
  not runnable in Claude Code. User must run one real pass to confirm the gates
  fire and no fabricated combat appears on the talky sample.
