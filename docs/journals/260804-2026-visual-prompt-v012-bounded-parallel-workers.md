# 2026-08-04 — visual-prompt v0.12.0: bounded-parallel Pass-2 workers

## What changed

Opt-in runner-level parallelism for Pass-2 scene expansion, shipped as 0.12.0
via plan `plans/260729-1645-bounded-parallel-scene-workers/` (all 5 phases in
one session, starting by closing the stale v0.10 plan as 0.11.0-shipped):

- `WORKER SUBMODE` + `PLAN-ONLY SUBMODE` TOML contracts (`--worker-manifest`,
  `--plan-only`); direct invocations never use either.
- `scripts/worker_manifest.py` (canonical #17): schema/frozen-snapshot
  validation, post-run ownership fence (`details.missing_scene_ids` = retry
  entry point), disjoint contiguous split.
- `check_run_legit --worker-manifest`: scenes-only workdir semantics (the
  `--no-video` skip-rule precedent applied to assembled outputs).
- `validate_artifacts --scene-ids`: subset scene gate for workers.
- `run-folder.sh`: `agy_harness()` (parameterized pexpect, modes
  full/plan/worker) + `VP_WORKERS` flow (head → freeze → fan-out → join →
  ONE bounded idempotent retry → merge → coverage → serial tail).
- RULE 0 gained its sole documented exception: runner-level workers; every
  worker session is still bound by RULE 0 internally.

## Why it went well

- TDD lock-first (Phase 1) kept the contract honest: strict xfail markers made
  each phase remove its own markers; the suite ended at 54 green / 0 xfail.
- Fail-closed fallback (any parallel failure → unchanged serial loop, partial
  valid scenes reused via cache keys) removed the risk of shipping a fragile
  fast path.
- Standalone smoke of the freeze/verify/legit/coverage chain caught an argv
  unpacking bug before any live run.

## Decisions to remember

- Retry = respawn the SAME immutable manifest (STEP 6 cache resume makes it
  idempotent); a reduced manifest would false-trip the ownership fence on
  already-written scenes.
- Workers never see `.work` of the coordinator; the frozen snapshot bundle is
  the only input surface (qa/bible/style/plan/history hashes fail-closed).
- Live Pass-2 wall-clock benchmark deferred to the first opt-in batch run —
  protocol + ≥1.8× criterion in the plan's `benchmark-report.md`.

## Unresolved

- Live speed number under Gemini per-minute rate limits (3 workers may need to
  tune to 2; gates never loosen).
- Cross-worker boundary duplication cost at join (first-pass similarity pass
  rate on the first opt-in run tells us the rewrite-loop tax).
- `.agents/` quarantine (260725 agy runtime dirs) — verified stale, recoverable
  via `.quarantine-260804/RESTORE.md`; delete whenever.
