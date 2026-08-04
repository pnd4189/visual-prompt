---
phase: 2
title: "Implement Isolated Scene Worker Mode"
status: completed
effort: "M"
---

# Phase 2: Implement Isolated Scene Worker Mode

## Overview
Add the worker submode for Pass-2 scene expansion. Each worker process receives a frozen hash bundle plus a disjoint scene-ID range, then writes only its assigned `scene-NNN.md` files. Any collision, stale hash, missing ID, timeout, crash, or unexpected file write must fail closed. This is the first code phase, so it must not weaken the existing serial path.

## Context Links
- `scripts/run-folder.sh:240-365`
- `scripts/validate_artifacts.py:288-341`
- `scripts/check_run_legit.py:168-222`
- `commands/visual-prompt.toml:432-499`

## Requirements
- Opt-in only; no behavior change when the flag/env is absent.
- Default enabled worker count is 3, capped by remaining scene rows.
- Each worker owns disjoint scene-ID ranges and no shared mutable state.
- Workers may only write their assigned `scene-NNN.md` files and local scratch.
- Worker submode runs pass `check_run_legit` under the Phase 1 pinned worker-run semantics (scenes-only workdir — no assembled/video/music outputs).
- Any new script under `scripts/` enters `CANONICAL_SCRIPTS` (`scripts/check_run_legit.py`) in the same commit; verify with `check_run_legit.py --purge-skill-dir .` → 0 rogue entries.

## Architecture
- Worker mode is an explicit `/visual-prompt` submode invoked through isolated top-level `agy` sessions, not a native subagent path.
- Worker input is a frozen snapshot of QA hash, bible hash, style hash, scene-plan hash, visual-history snapshot, and the assigned scene IDs.
- Worker output is limited to assigned scene files plus bounded local scratch, with fail-closed exit on any mismatch.
- Worker submode must stop after scene validation; it must not run music, assembly, similarity/history publication, final self-audit, or batch completion markers.

## Related Code Files
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/run-folder.sh`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/commands/visual-prompt.toml`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/SKILL.md` (RULE 0 runner-level exception clause + worker submode note)
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/adapters/codex/visual-prompt/SKILL.md`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/adapters/claude-code/visual-prompt/SKILL.md`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/tests/test_prompt_contracts.py`
- Modify or add a canonical validator under: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/`

## Implementation Steps
1. Add command parsing for the immutable worker manifest plus runner opt-in/env parsing and worker count.
2. Add isolated worker workdirs and per-worker ownership manifests.
3. Enforce write-only-to-assigned-scene paths using a deterministic pre/post filesystem diff and abort on collision or stale snapshot.
4. Add bounded targeted retry for worker-local failures only.
5. Keep the existing serial code path byte-for-byte equivalent when opt-in is off.
6. Register any new `scripts/` file in `CANONICAL_SCRIPTS` in the same commit, and add the RULE 0 runner-level exception clause + worker submode note to root `SKILL.md`.

## Todo List
- [x] Parse worker opt-in and default count.
- [x] Add ownership checks and write fences.
- [x] Add frozen snapshot validation.
- [x] Add bounded retry and timeout handling.
- [x] Adapt `check_run_legit` to the pinned worker-run semantics (scenes-only workdir).
- [x] Register new script in `CANONICAL_SCRIPTS`; update root `SKILL.md` RULE 0 exception.
- [x] Preserve serial path.

## Success Criteria
- [x] A worker can only produce the scene files assigned to its range.
- [x] Collision, stale-hash, timeout/crash, and unexpected-write cases exit non-zero.
- [x] Serial mode remains unchanged when the opt-in flag/env is absent.

## Completion Notes (2026-08-04)
- New canonical `scripts/worker_manifest.py`: `--validate` (schema 1 + frozen
  bundle sha256 checks, exit 2 on any drift), `--verify-run` (ownership fence:
  work_dir holds exactly the assigned scene files; violations JSON includes
  `details.missing_scene_ids` as the bounded-retry entry point), and `--split`
  (disjoint contiguous ranges, capped by row count — landed here with the
  script, consumed by Phase 3 coordinator).
- `check_run_legit.py`: `--worker-manifest` switches to scenes-only semantics
  (runtime-code scan + ownership stay; assembled image/video/boilerplate checks
  skipped per the --no-video skip-rule precedent; report gains `worker_run`).
- `validate_artifacts.py`: `check_scenes(..., assigned_ids)` + `--scene-ids`
  CLI flag for the worker subset gate (assigned ids must exist in the plan).
- `run-folder.sh`: `VP_WORKERS` parse/validate (default 1 = serial; integer
  1..16, cap by remaining scene rows is Phase 3's split). Fan-out wiring is
  Phase 3; timeout/retry spawn loop rides the parameterized pexpect harness.
- Root `SKILL.md`: RULE 0 runner-level exception clause + scripts count 16.
  TOML STEP 6: worker-submode precondition pointer.
- xfail markers removed for the 5 phase-02 protocol tests; suite 51 passed +
  2 xfailed (phase-03 fan-out announce + join-before-marker).

## Risk Assessment
- High: race or collision corrupts shared `.work/`. Mitigation: per-worker workdirs, ownership manifests, and write fences.
- Medium: startup overhead erodes gains on small batches. Mitigation: cap worker count to available scene rows.
- Medium: cross-worker boundary effects — adjacent-range workers generate independently from the frozen snapshot; continuity relies on scene-plan rows, and cross-worker duplication is caught only at join (rewrite-loop cost). Mitigation: join-time similarity gate unchanged; watch first-pass pass rate in Phase 4.

## Security Considerations
- Do not accept arbitrary paths from worker input.
- Keep worker scratch isolated from coordinator-owned artifacts.

## Rollback
- Disable the opt-in flag/env and route all files through the existing serial path.

## Next Steps
- Phase 3 can only wire fan-out/join after the worker protocol is stable.
