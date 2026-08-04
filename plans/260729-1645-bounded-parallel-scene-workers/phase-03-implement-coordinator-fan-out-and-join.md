---
phase: 3
title: "Implement Coordinator Fan-out and Join"
status: pending
effort: "M"
---

# Phase 3: Implement Coordinator Fan-out and Join

## Overview
Teach the coordinator to freeze Pass-2 inputs, fan out the worker ranges, and join the results before any shared-state write. The coordinator alone handles QA/bible/style/history snapshots, music, assembly, similarity/history publish, completion marker, and the final gates. This phase turns the worker protocol into a bounded parallel batch runner without changing the default serial path.

## Context Links
- `scripts/run-folder.sh:21-30, 240-365, 388-720`
- `commands/visual-prompt.toml:377-447, 509-733`
- `scripts/validate_artifacts.py:288-341, 344-459, 478-517`
- `plans/reports/researcher-260729-agy-antigravity-subagents.md:61-83`

## Requirements
- Coordinator remains the only writer of QA, bible/history, completion marker, and final outputs.
- Completion marker may be written only after all workers join and all final gates pass.
- Partial completion must survive worker failure without masking missing IDs.
- No new external dependency.

## Architecture
- Coordinator snapshots the frozen inputs, splits the scene-plan into disjoint worker ranges, and waits on worker exit codes plus coverage.
- Worker output is accepted only if the join set exactly covers the expected scene IDs with no duplicates or gaps.
- The existing gates still run after join; parallelism must not weaken them.

## Related Code Files
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/run-folder.sh`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/commands/visual-prompt.toml`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/tests/test_prompt_contracts.py`

## Implementation Steps
1. Freeze the pre-worker hashes and snapshots before dispatch.
2. Spawn up to 3 worker sessions on disjoint scene ranges and collect their exit codes. Vehicle = parameterized reuse of the existing pexpect harness in `run-folder.sh` (per-worker batch_token, workdir, completion markers, direct-redirect logs — no tee; keep `--add-dir` bibles). Do NOT regress to `agy -p` one-shot: the WIP committed in Phase 0 replaced it with this harness exactly to fix the yield-turn/approval incident class (user decision 2026-08-04).
3. Verify full range coverage, no duplicates, and no unexpected files before merge.
4. Keep QA, bible/style/history publish, assembly, similarity, and completion marker strictly after join.
5. Preserve the current retry/fail-closed behavior for timeout, crash, and partial completion.

## Success Criteria
- [ ] Completion marker appears only after join + final gates.
- [ ] No worker can publish history or marker.
- [ ] Partial completion and crash cases fail closed without leaking to shared state.

## Todo List
- [ ] Add coordinator snapshot freeze.
- [ ] Parameterize the pexpect harness per worker (batch_token, workdir, markers, direct-redirect logs).
- [ ] Add fan-out range split and join.
- [ ] Add coverage/duplicate checks.
- [ ] Keep all post-join gates coordinator-only.
- [ ] Verify serial fallback remains unchanged.

## Risk Assessment
- High: orphaned or hung workers. Mitigation: hard per-worker timeout plus cleanup on join failure.
- High: premature marker emission. Mitigation: marker write gated behind the final post-join checks.
- Medium: cross-worker boundary duplication surfaces only at join, spending rewrite loops. Mitigation: similarity gate runs unchanged post-join; track first-pass pass rate in Phase 4.

## Security Considerations
- Do not let workers write coordinator-owned artifacts.
- Treat any unexpected file outside ownership as a hard failure.

## Rollback
- Route the runner back to serial execution by clearing the opt-in flag/env.

## Next Steps
- Phase 4 validates throughput, gate parity, and rollout readiness.
