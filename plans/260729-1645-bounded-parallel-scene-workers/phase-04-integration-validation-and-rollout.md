---
phase: 4
title: "Integration Validation and Rollout"
status: pending
effort: "M"
---

# Phase 4: Integration Validation and Rollout

## Overview
Validate that opt-in parallel mode is faster without weakening gates, then update the user-facing docs and release notes. The direct skill contract can stay serial, but the batch driver needs a documented runner-level exception and a rollout guard. This phase also proves the rollback path is just a config flip plus restart.

## Context Links
- `README.md:30-40`
- `scripts/run-folder.sh:21-30, 332-365, 518-720`
- `tests/test_prompt_contracts.py:782-923`
- `plans/reports/researcher-260729-agy-antigravity-subagents.md:69-83`

## Requirements
- Benchmark must show Pass-2 wall-clock ≥ ~1.8× serial on the same local batch; shortfall from rate limits → tune `VP_WORKERS` down, never loosen gates.
- Gate coverage must stay identical or stronger; no threshold loosening.
- Documentation must explain that the new mode is opt-in and the default serial path remains unchanged.
- Deployment to the active batch happens only after tests pass and the driver is explicitly restarted.

## Architecture
- Measure serial vs 3-worker opt-in on a controlled local batch with the same gates enabled.
- Publish results only after the coordinator path proves it still owns final gates and markers.
- Update the public docs that explain the runner behavior; keep the default direct flow unchanged.

## Related Code Files
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/README.md`
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/SKILL.md` (workflow docs + version bump)
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/gemini-extension.json` (version bump)
- Modify: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/scripts/run-folder.sh`
- Read/update: `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt/tests/test_prompt_contracts.py`

## Implementation Steps
1. Run the targeted test suite against both serial and opt-in worker modes.
2. Run the throughput benchmark on one controlled local batch and record the delta.
3. Bump the release version in all three places (SKILL.md frontmatter, gemini-extension.json, TOML prompt header — currently 0.11.0) and update the user-facing docs (SKILL.md workflow section + README) to describe the opt-in worker mode and unchanged default path.
4. Verify rollback by disabling the opt-in switch and rerunning the same batch serially.
5. Require an explicit restart before enabling the new mode in the active batch driver.

## Success Criteria
- [ ] Benchmark shows Pass-2 ≥ ~1.8× serial wall-clock on the same batch (or `VP_WORKERS` tuned down with the rate-limit reason recorded — gates never loosened).
- [ ] Version bumped in SKILL.md + gemini-extension.json + TOML header.
- [ ] No gate weakens compared with serial mode.
- [ ] Docs state default serial behavior plus opt-in worker mode.
- [ ] Rollback is a config flip, not a data migration.

## Todo List
- [ ] Run serial-vs-parallel test matrix.
- [ ] Capture benchmark numbers (target Pass-2 ≥ ~1.8×) and gate parity.
- [ ] Bump version in SKILL.md + gemini-extension.json + TOML header; update SKILL.md workflow docs + README.
- [ ] Verify rollback path.
- [ ] Approve rollout only after explicit restart.

## Risk Assessment
- High: benchmark overfits one machine. Mitigation: record relative improvement, not absolute SLO.
- High: docs drift from behavior. Mitigation: update the docs in the same phase as the rollout proof.

## Security Considerations
- No new dependency or broader filesystem permission is allowed in rollout.
- Keep worker isolation and fail-closed gates in place during all benchmark runs.

## Rollback
- Disable the opt-in switch and restart the batch driver; the serial path must remain the fallback.

## Next Steps
- Ship only after the benchmark, tests, and docs all agree on the same behavior.
