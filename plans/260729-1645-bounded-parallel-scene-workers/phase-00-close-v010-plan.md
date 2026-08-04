---
phase: 0
title: "Close v0.10 Anti-Repetition Plan (Prerequisite)"
status: completed
effort: "S"
---

# Phase 0: Close v0.10 Anti-Repetition Plan (Prerequisite)

## Overview

Plan 260714-1044 (v0.10 anti-repetition) has phases 2-6 already implemented and
shipped (similarity gate, visual-history, music-plan persistence, TOML wiring —
verified by audit 260804-1910), but was never formally closed. Its gate
verification surface must settle before any parallel worker code lands
(this plan's frontmatter `blockedBy`).

## Context Links
- `plans/260714-1044-vp-anti-repetition-optimal-upgrade/plan.md`
- `plans/reports/audit-260804-1910-vp-gates-speed-quality-report.md`
- `scripts/run-folder.sh` (uncommitted WIP), `scripts/check_run_legit.py` (uncommitted WIP)

## Requirements
1. Commit uncommitted WIP (+636 lines): targeted repair batches
   (`VP_REPAIR_CHUNK_SIZE`), `check_run_legit.py --report-json`, tests (+116),
   TOML/adapter changes. Conventional commits.
2. Close v0.10 phase-01. It partially ran on 2026-07-20 (`.quarantine-260713/`
   exists with the chap16 fixture) — reconcile and finish, do NOT re-run its
   stale recipe ("move every untracked except plans/" — today's untracked
   includes legit `docs/journals/*` and `plans/**`). Quarantine the current
   junk inventory into a fresh `.quarantine-260804/` (recoverable, never delete):
   - Move: `tmp_work5`, `tmp_work6`, `tmp_work_img_261`, `tmp_work_music`,
     `tmp_work_qa`, `tmp_work_qa_231`, `tmp_work_qa_251`, `tmp_work_qa_261`,
     `tmp_work_qa_281`, `tmp_work_qa_dao_si`, `.staging-chap6`, `scenes`,
     `scenes-051-100`, `OTHERS`, `conductor`, `scratch`, `.work`,
     `blank_16_9.png`, `selected_40_prompts.txt`, `pipeline_execution.log`,
     `Binh_Thien_Sach_0031_0040_vi_{image,music,video}_prompts.txt`.
   - Confirm before moving: `.agents/` (may be live runtime state; if moved,
     document the restore path).
   - Keep in place: every `.quarantine-*` dir — already quarantine;
     `.quarantine-auto` is LIVE (the purge gate writes there);
     `.quarantine-260713/local_chap16.txt` is the phase-07 acceptance fixture.
3. Execute v0.10 phase-07 release discipline: record that the work shipped as
   **0.11.0** (SKILL.md + gemini-extension.json + TOML prompt header already
   synced at 0.11.0; no 0.10.0 release commit exists) and fix phase-07's
   0.10.0 references while updating statuses; update v0.10 plan.md phase
   statuses + frontmatter to completed; fix memory note
   `vp-0100-anti-repetition-plan-ready` (claims "not yet executed" — stale).
4. Run contract test suite (40 tests) + py_compile + bash -n + TOML parse clean.

## Todo List
- [x] Commit WIP (check_run_legit report-json, run-folder targeted repair, tests)
      + plan artifacts (`plans/260714-1044*/`, `plans/260729-1645*/`,
      `plans/reports/*`, `docs/journals/*`) — do NOT commit `.agents/`, `scratch/`.
      → commits 202aa10, 69922da, 8a8cc98.
- [x] Quarantine root junk per Requirements §2 inventory (protect every
      `.quarantine-*` dir; confirm `.agents/` before moving).
      → 24 items → `.quarantine-260804/` + RESTORE.md; `.agents/` verified
      stale (live agy session had different CWD).
- [x] Record shipped-0.11.0, close v0.10 plan.md, fix memory note (phase-07).
      → v0.10 plan.md + phases 01/02/07 closed with reconciliation notes;
      memory `vp-0100-anti-repetition-plan-ready` + MEMORY.md updated.
- [x] Full test/syntax pass.

## Success Criteria
- `git status` clean on tracked skill files; root holds only canonical entries
  plus `.quarantine-*` dirs.
- v0.10 plan.md status: completed; all 7 phases closed; version recorded as
  shipped 0.11.0.
- 40 tests + syntax checks pass.

## Rollback
N/A — hygiene + commits only; quarantine is recoverable.

## Next Steps
Phase 1 (lock contracts + regression tests) may start.
