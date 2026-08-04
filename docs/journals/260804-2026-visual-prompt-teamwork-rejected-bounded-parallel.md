# Visual Prompt — /teamwork-preview auto-trigger rejected; bounded-parallel confirmed

**Date**: 2026-08-04
**Severity**: Low (decision record, no code change)
**Component**: visual-prompt skill — Pass-2 parallelization strategy
**Status**: Decided, not implemented

## What Happened

With Gemini Ultra quota plentiful, the idea was to have `/visual-prompt` on agy
CLI auto-trigger agy's built-in `/teamwork-preview` (subagent teams:
explorer/reviewer/auditor/challenger/test_writer/spec_miner, verified present in
the 2026-08-03 agy binary) to speed up scene expansion.

Scout evidence killed it: RULE 0 bans in-run delegation after real bypass
incidents; teamwork's built-in workers are blind to the skill contract
(anchors/10-section/frontmatter/cache keys); `.work/` has no write fences under
teamwork; headless `agy -p` (the batch path) likely dies on yield-turn in a
multi-turn orchestration; and `check_run_legit` cannot distinguish subagent-written
scenes from parent-written ones — a bypass that would go undetected.

## Decision

Vehicle = existing plan `plans/260729-1645-bounded-parallel-scene-workers/`:
runner-level coordinator spawns 3 isolated full `agy` sessions (worker submode,
full contract) on disjoint scene ranges; all gates stay coordinator-owned;
serial path unchanged without `VP_WORKERS`. Added Phase 0 to first close the
never-closed v0.10 anti-repetition plan (commit WIP, root quarantine, release
discipline).

Report: `plans/reports/brainstorm-260804-1927-vp-teamwork-preview-rejected-bounded-parallel-report.md`

## Why It Matters

Quota abundance does not change the reason RULE 0 exists: delegation *by the
running model* is the mechanism that produced the bypass incidents. Parallelism
belongs at the runner level, where fences and gates are deterministic.

## Open / Not Verified

- Whether `/teamwork-preview` survives headless `-p` multi-turn at all (not
  needed for the chosen path; spike only if B is ever relitigated).
- Real per-minute rate limit of 3 concurrent Gemini 3.1 Pro (High) sessions on
  Ultra — Phase 4 benchmark.
