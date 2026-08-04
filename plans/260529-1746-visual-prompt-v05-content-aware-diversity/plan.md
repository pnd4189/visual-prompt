---
title: "Visual Prompt v0.5 — Content-Aware Scene Diversity"
description: >-
  Make scene diversity content-aware (measure action density, no forced combat
  quota on talky stories), fix the synopsis-fragment bug, add two deterministic
  enforcement gates (plan-level variation + assembly-level depth with
  auto-regenerate), add a gold-standard few-shot example to the image expander,
  and an optional --epic escape hatch.
status: completed
priority: P1
branch: "main"
tags:
  - skill
  - agy-cli
  - prompts
  - scene-diversity
  - enforcement
blockedBy: []
blocks: []
created: "2026-05-29T10:46:40.168Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt v0.5 — Content-Aware Scene Diversity

## Overview

v0.4 added strong scene-diversity wording but it is model-honored only, and its
35-45% action target is wrong for talky stories. Verify proved the sample novel
is ~22:1 talk:combat — forcing combat quotas would fabricate plot. v0.5 makes
diversity targets content-aware, draws anti-monotony from VISUAL variety (camera/
scale/group-of-present-chars/object-insert/flashback) instead of fake combat,
fixes the synopsis-fragment bug, and adds deterministic backstops so degraded
output cannot pass silently.

Brainstorm: [`../reports/brainstorm-260529-content-aware-scene-diversity.md`](../reports/brainstorm-260529-content-aware-scene-diversity.md)

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Scene-Planner Content-Aware Diversity + Synopsis Fix](./phase-01-scene-planner-content-aware-diversity-synopsis-fix.md) | Completed |
| 2 | [Plan-Level Variation Gate](./phase-02-plan-level-variation-gate.md) | Completed |
| 3 | [Assembly-Level Depth Gate + Auto-Regenerate](./phase-03-assembly-level-depth-gate-auto-regenerate.md) | Completed |
| 4 | [Expander Gold Example + Epic Flag](./phase-04-expander-gold-example-epic-flag.md) | Completed |
| 5 | [Validation Docs Version-Sync](./phase-05-validation-docs-version-sync.md) | Partial (scripts/docs/version done; LLM end-to-end run pending — needs Agy CLI) |

## Key Decisions

| Topic | Decision |
|---|---|
| Diversity targets | Content-aware. `calc_scene_count.py` emits `action_density` (low/med/high) + recommended mix band; planner consumes it. No global combat quota. |
| Anti-monotony (talky) | Visual variety: camera/angle/scale, group tableaus of characters ACTUALLY present, object/detail inserts, flashback/symbolic shots, weather/time variation. No fabricated combat. |
| v0.4 combat vocab | KEPT intact for stories/scenes that genuinely have action; only the hard global percentage is removed. |
| Synopsis bug | Planner must emit coherent 1-line synopsis; plan-gate rejects fragments. |
| Plan gate | New `scripts/validate_scene_plan.py`: reject repeated tag+characters+location triples within window + invalid/fragment synopsis. |
| Depth gate | Extend `assemble_outputs.py` to emit per-block violations (missing header / word count / negative count). Regen loop lives in toml orchestration, max-retry capped. |
| Gold example | Template (`visual-prompt-template.md`) ALREADY has image+video examples (lines ~86-99). Do NOT embed a duplicate; make `prompt-expander-image.md` explicitly require reading + adhering to the template example (DRY). |
| --epic | Optional flag amplifies scale when user wants it AND story supports it. |
| Video length cap | Veo3/Google Flow hard limit is 4000 chars. Video prompt HARD CAP = 3800 chars (~600-630 words) — replaces the old 900-word cap. Same number in expander + depth gate (DRY). Image prompts unaffected (no Flow limit). |
| New files | Exactly one: `scripts/validate_scene_plan.py`. Density folds into calc; depth folds into assemble. |
| Version | Bump SKILL.md + gemini-extension.json to 0.5.0 (sync both per memory). |

## Validation Gates

- `calc_scene_count.py` emits a stable `action_density` + mix band; unit-smoke for low/high density inputs.
- `validate_scene_plan.py` flags adjacent-duplicate triples and fragment synopses on a synthetic plan fixture; clean plan passes.
- `assemble_outputs.py` violations list catches a shallow block (missing headers / <350 words) and passes a rich block.
- Re-run the real sample (`tmp_work5/chapters_qa.json`-derived) with `--force-redo`; assembled image file has 10 sections/block, no adjacent-duplicate triples, no fragment synopsis, and NO fabricated combat for the talky source.
- Static grep: no global "35-45% action" hard quota remains as an unconditional default.
- Every assembled video block is <= 3800 chars (verify max block length on the sample run; must paste into Google Flow without "Prompt too long").

## Dependencies

- Builds on v0.4 (`260529-1607-...`, status: completed). No blocker.
- Surgical edits to existing prompt/script/command/docs files + one new validator script.

## Validation Log

### Session 1 (2026-05-29)

Verification (Full tier, 5 phases): all file paths VERIFIED — `calc_scene_count.py`,
`assemble_outputs.py`, `scene-planner.md`, `prompt-expander-image.md`,
`prompt-expander-video.md`, `visual-prompt-template.md`, `negative-lists.md`,
`visual-prompt.toml`, `SKILL.md`, `gemini-extension.json` all exist;
`scripts/validate_scene_plan.py` correctly absent (to create). Failed: 0.

Confirmed decisions:
- **action_density thresholds:** low `<2`, medium `2-6`, high `>6` combat-hits per
  1k words. Action band: low 5-15%, medium 20-30%, high 35-45%. (Sample = ~0.13 → low.)
- **Negative-item floor (depth gate):** `20` (not 14 — layers 1+3+4 always-include = 19;
  20 catches truncation without false positives).
- **Video char cap:** `3800` (margin under Flow/Veo3 4000 limit for counting drift).
- **Gold example:** template already has examples; expander must reference + adhere
  to them, NOT embed a duplicate (DRY). Phase 4 reduced to a reference/adherence rule.

### Whole-Plan Consistency Sweep (Session 1)

PASS — zero unresolved contradictions. Verified: negative floor `14` fully
superseded by `20` (only survives in log + change marker); `900`-word cap appears
only as historical context for the `3800`-char replacement; `35-45%` action
remains only as the conditional high-density band, default removed everywhere;
gold-example is reference-not-embed across all files. Eligible for `/ck:cook`.

### Session 2 — Implementation (/ck:cook, 2026-05-29)

All 5 phases implemented. Deterministic verification PASS:
- `calc_scene_count.py`: density emitted; sample → `low` (0.73 hits/1k), combat
  fixture → `high`, `--epic` bumps low→medium; old keys (images/videos/wordcount/
  source) intact; override path works.
- `validate_scene_plan.py` (new): real sample flags 14 fragment synopses + adjacent
  dups (exit 2); clean plan exit 0; missing file exit 1.
- `assemble_outputs.py`: depth gate flags shallow image (missing headers / <350w /
  <20 negatives), video >3800 chars, bad beat count; rich block clean; `.txt`
  format byte-compatible (`--- SCENE NNN ---`); `violations` in JSON.
- All 3 scripts `py_compile` clean.
- Static grep: no unconditional 35–45% action default (only conditional high band +
  negation text remain); 900-word cap only as historical context.
- Version synced 0.5.0 in BOTH SKILL.md + gemini-extension.json (gemini was stale
  at 0.3.0 — the foot-gun — now fixed).

NOT verified (environment limitation): the full `--force-redo` end-to-end LLM run
(Phase 5 step 2–3) needs the Agy CLI LLM loop to generate ~116 scenes — cannot run
in Claude Code. Orchestration wiring (toml STEP 5.5 + STEP 7 loops) is documented
but only exercises at runtime. **User must run one real `--force-redo` pass in Agy
to confirm gates fire and no fabricated combat appears on the talky sample.**

Stale `part1*/part2*` deletion deferred to user confirmation (Phase 5 step 6).

## Out of Scope

New output files, reference-image workflow, new runtime deps, QA/TTS/bible/music
architecture changes.
