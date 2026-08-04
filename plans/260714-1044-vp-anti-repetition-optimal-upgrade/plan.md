---
title: "visual-prompt 0.10.0 — anti-repetition gates + visual-history + music-plan persistence"
description: "Outcome-based similarity gates (plan/pipeline/driver), dynamic per-series visual-history, music segmentation persistence, cheap driver retry. Kills copy-paste/template output on agy CLI."
status: completed
priority: P1
branch: "main"
tags: [visual-prompt, anti-repetition, gates, agy]
blockedBy: []
blocks:
  - "plans/260729-1645-bounded-parallel-scene-workers/plan.md"
created: "2026-07-14T03:51:55.458Z"
createdBy: "ck:plan"
source: skill
---

# visual-prompt 0.10.0 — anti-repetition gates + visual-history + music-plan persistence

## Overview

Source (all design decisions locked):
`plans/reports/brainstorm-260714-1044-vp-anti-repetition-optimal-upgrade-report.md`

Evidence: chap16 output had 38-106 exact-dup pairs/field, stride +11 block copy
(41≡52≡63≡74) — evaded window-10 plan gate; no cross-scene gate existed post-assemble.

Strategy: deterministic gates measure OUTCOME (model can't negotiate); prompt
constraints are soft layer only; cross-run repetition handled by per-series
visual-history file; hardcoded series-specific avoid-lists (uncommitted +210
lines) get REPLACED by dynamic mechanism.

Key locked decisions:
- FAIL policy: pair_copy (≥2 fields sim ≥0.95 same scene pair) ≥2 pairs, OR
  ≥5 exact (≥0.995) pairs in one field. Soft band 0.60-0.95 = WARN only.
- Retry: similarity-only fail → re-run WITHOUT --force-redo (resume + targeted
  rewrite); legit-gate fail / missing output → --force-redo (unchanged).
- Visual-history: `~/.gemini/bibles/<series>-visual-history.md`, rolling cap
  ~150 lines/section, updated STEP 7.8 (post content-safety), --series only.
  Semantics: ban verbatim reuse of wording/motifs, NOT locations.
- Music: persist `.work/music-plan.md` (closes official SKILL.md limitation).
- New script MUST enter CANONICAL_SCRIPTS or purge gate quarantines it.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Root Cleanup Quarantine](./phase-01-root-cleanup-quarantine.md) | Completed |
| 2 | [Similarity Gate Script](./phase-02-similarity-gate-script.md) | Completed |
| 3 | [Plan Gate Synopsis Dedup](./phase-03-plan-gate-synopsis-dedup.md) | Completed |
| 4 | [Prompt Hardening Dynamic History](./phase-04-prompt-hardening-dynamic-history.md) | Completed |
| 5 | [TOML Wiring Music Plan Persistence](./phase-05-toml-wiring-music-plan-persistence.md) | Completed |
| 6 | [Batch Driver Integration](./phase-06-batch-driver-integration.md) | Completed |
| 7 | [Verify Release 0-10-0](./phase-07-verify-release-0-10-0.md) | Completed |

Order: 1 → 2 → 3 → 4 → 5 → 6 → 7 (2-4 could parallel but same-session
sequential is simpler; 5 depends on 2+3+4; 6 depends on 2; 7 last).

## Acceptance (from report §8)

1. New script on chap16 output: FAIL, Camera exact-dup ≈38 pairs (matches full_report.md).
2. Stride-11 plan fixture → duplicate_synopsis flagged.
3. py_compile / tomllib parse / bash -n all clean.
4. Version 0.10.0 synced: SKILL.md + gemini-extension.json + TOML header.
5. 2 commits: chore(cleanup) + feat(0.10.0).
6. Post-release (first real runs): exact-dup = 0, pair_copy = 0; music cache hit on re-run;
   visual-history created after --series run.

## Dependencies

None. Symlink install = changes live immediately on commit (no redeploy, Linux).

## Closure (2026-08-04)

Closed by plan `plans/260729-1645-bounded-parallel-scene-workers/` Phase 0.
Audit `plans/reports/audit-260804-1910-vp-gates-speed-quality-report.md`
confirmed phases 2-6 shipped; Phase 0 reconciled the remainder:

- Shipped as **0.11.0** — no 0.10.0 release commit exists; SKILL.md,
  gemini-extension.json, and TOML prompt header were already synced at 0.11.0.
- Phase 1 root cleanup superseded: final quarantine executed as
  `.quarantine-260804/` (see its `RESTORE.md`).
- Re-verified 2026-08-04: 40 contract tests pass; py_compile + tomllib +
  `bash -n` clean; `check_run_legit.py --purge-skill-dir .` → 0 rogue;
  chap16 fixture now post-repair (exit 0, Camera exact = 0 — original failing
  state preserved only in `.quarantine-260713/full_report.md`).
