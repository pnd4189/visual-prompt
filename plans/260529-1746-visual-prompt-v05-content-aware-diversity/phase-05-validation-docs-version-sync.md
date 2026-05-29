---
phase: 5
title: "Validation Docs Version-Sync"
status: partial
priority: P1
effort: "2-3h"
dependencies: [1, 2, 3, 4]
---

# Phase 5: Validation Docs Version-Sync

## Overview

End-to-end validation on the real talky sample, docs update for the new
behavior/flags, and the mandatory two-place version bump to 0.5.0.

## Requirements

- Functional: a real `--force-redo` run on the sample produces an assembled image
  file with 10 sections/block, no adjacent-duplicate triples, no fragment
  synopsis, and NO fabricated combat.
- Functional: every assembled video block is <= 3800 chars (pastes into Google
  Flow / Veo3 without "Prompt too long (max 4000 characters)").
- Functional: scripts smoke-tests pass (calc density, validate_scene_plan,
  assemble violations).
- Functional: docs reflect content-aware diversity + `--epic` + the two gates.
- Non-functional: version synced in BOTH `SKILL.md` and `gemini-extension.json`
  (Agy CLI reads the manifest) — see memory `version-bump-two-places`.

## Architecture

- Use the existing `tmp_work5/chapters_qa.json`-derived input (or `part1.txt`) as
  the validation corpus; run the pipeline end-to-end with `--force-redo`.
- Stale outputs `part1*.txt` / `part2*.txt` are NOT pipeline artifacts — delete
  them after confirming the real run supersedes them (avoid confusing future runs).

## Related Code Files

- Modify: `SKILL.md` (version 0.5.0; document density-aware diversity, gates, --epic)
- Modify: `gemini-extension.json` (version 0.5.0 — sync)
- Modify: `README.md`, `HUONG-DAN-SU-DUNG.md` (behavior + flag docs)
- Modify: `docs/journals/` (new entry via /ck:journal at close)
- Delete (after verify): stale `part1*.txt`, `part2*.txt`, `part2_copy.txt`

## Implementation Steps

1. Run all script smoke-tests (calc density low/high, validate_scene_plan
   pass/fail, assemble violations pass/fail).
2. Full `--force-redo` run on the sample; inspect assembled image/video files.
3. Confirm success criteria: 10 sections/block, no adjacent dupes, coherent
   synopses, no fabricated combat, depth gate clean.
4. Update SKILL.md + gemini-extension.json to 0.5.0 (both).
5. Update README.md + HUONG-DAN-SU-DUNG.md for new behavior + `--epic`.
6. After confirming the real run, remove stale hand-made `part1*/part2*` files.
7. Static grep: no unconditional "35-45% action" default remains.

## Success Criteria

- [ ] End-to-end run on the talky sample passes all gates with no fabricated combat.
- [ ] Max video block on the sample run is <= 3800 chars (Flow paste-safe).
- [ ] All script smoke-tests pass.
- [ ] SKILL.md and gemini-extension.json both at 0.5.0.
- [ ] README + HUONG-DAN-SU-DUNG document content-aware diversity + `--epic`.
- [ ] Stale part1/part2 files removed.

## Risk Assessment

- Risk: deleting part1/part2 loses something the user still wants.
  Mitigation: confirm with user before deletion; they are confirmed non-pipeline stale outputs.
- Risk: version drift between the two files (recurring foot-gun).
  Mitigation: bump both in the same change; grep both after.
