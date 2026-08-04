---
phase: 1
title: "Lock Contracts and Regression Tests"
status: completed
effort: "S"
---

# Phase 1: Lock Contracts and Regression Tests

## Overview
Freeze the current serial baseline before touching orchestration. The repo still says parent-only micro-batches, no subagents/parallel generation, and fail-closed validation [README.md:30-33][scripts/run-folder.sh:21-30][scripts/validate_artifacts.py:288-341][plans/reports/researcher-260729-agy-antigravity-subagents.md:69-83]. This phase turns the new opt-in worker contract into tests first.

## Context Links
- `plans/260714-1044-vp-anti-repetition-optimal-upgrade/plan.md`
- `README.md:30-33`
- `scripts/run-folder.sh:21-30, 332-365, 688-720`
- `scripts/validate_artifacts.py:288-341, 344-459, 478-517`

## Requirements
- Default single-mode stays unchanged unless the new opt-in flag/env is present.
- Define a command-level worker submode that accepts an immutable worker manifest and exits after Pass-2 scene validation.
- Tests must prove workers own disjoint scene-ID ranges and may only write assigned `scene-NNN.md` files.
- Tests must fail closed on collision, stale snapshot/hash, timeout/crash, partial completion, and completion marker before join+gates.
- Tests must pin worker-run legit semantics: which gates apply to a partial worker workdir (scenes only — no assembled/video/music outputs), mirroring the `--no-video` skip-rule precedent so `check_run_legit` never false-fires on a worker run.
- No new external dependency.

## Architecture
- Use regression tests to lock the current runner contract and define the future worker protocol.
- Coordinator remains sole writer of QA, bible/style/history, completion marker, and final outputs.
- Parallel mode is runner-level only; direct skill generation stays parent-only.

## Related Code Files
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/tests/test_prompt_contracts.py`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/commands/visual-prompt.toml`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/adapters/codex/visual-prompt/SKILL.md`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/adapters/claude-code/visual-prompt/SKILL.md`
- Read: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/run-folder.sh`
- Read: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/validate_artifacts.py`
- Read: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/check_run_legit.py`

## Implementation Steps
1. Lock the worker-manifest schema, command flags, Pass-2-only exit contract, and unchanged serial behavior in tests.
2. Add worker ownership/collision fixtures, stale-hash fixtures, timeout/crash coverage, partial-completion coverage, and worker-run legit-semantics coverage (scenes-only workdir).
3. Add a benchmark hook or smoke fixture that can be reused in the rollout phase.
4. Run the focused test slice until the new contract fails for the right reasons.

## Success Criteria
- [x] Default serial path still passes unchanged when the opt-in mode is disabled.
- [x] New tests fail on collision, stale snapshot, crash/timeout, and marker-before-gates.
- [x] Worker-run legit semantics pinned: valid partial worker workdir passes; full-pipeline expectations unchanged.
- [x] Benchmark harness exists without weakening any gate.

## Todo List
- [x] Pin current serial path in tests.
- [x] Add collision and stale-snapshot assertions.
- [x] Add crash/timeout and partial-completion assertions.
- [x] Add marker-ordering assertion.
- [x] Pin worker-run legit semantics (partial worker workdir passes; full-pipeline expectations unchanged).
- [x] Capture baseline test output for later comparison.

## Completion Notes (2026-08-04)
- TOML: `WORKER SUBMODE (Pass-2 only, batch-runner-invoked)` section +
  `--worker-manifest <path>` flag (flag 13, mutex vs media/style/series flags);
  adapters (codex + claude-code) document the submode and that adapters never
  start workers.
- Tests: `WorkerProtocolContractTests` + `BenchmarkSmokeTests` in
  `tests/test_prompt_contracts.py`. Suite = 44 passed + 7 xfailed(strict).
- Deviation (recorded): the 7 worker-protocol tests are `xfail(strict=True)`
  instead of plain-failing — same contract lock, suite stays green, and any
  accidental early pass fails the suite until Phase 2/3 removes the markers.
- xfail markers to remove: phase-02 (manifest validate/verify-run, worker-run
  legit semantics, CANONICAL_SCRIPTS membership), phase-03 (split ranges,
  VP_WORKERS fan-out announce, join-before-marker runner lock).
- Baseline captured: `baseline-test-output.txt` in this phase directory.

## Risk Assessment
- High: tests overfit log text instead of state. Mitigation: assert files, hashes, and exit codes first.
- Medium: benchmark flakiness. Mitigation: compare relative wall-clock on one controlled local batch only.

## Security Considerations
- Tests must prove no unexpected writes outside assigned scene files or `.work/` scratch.
- No test should require broader filesystem or network access.

## Rollback
- Remove only the new regression cases if the worker contract is revised.
- Keep the existing serial baseline untouched.

## Next Steps
- Phase 2 can start only after these tests describe the worker boundary clearly.
