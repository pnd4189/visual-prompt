---
phase: 5
title: "End-to-End Test"
status: partial-user-test-pending
priority: P1
effort: "1d"
dependencies: [2, 4]
---

# Phase 5: End-to-End Test

## Overview

Real-world validation. Run `/visual-prompt` on actual Vietnamese xianxia files: 1 short (single chapter, ~2k words), 1 medium (full 1h audio ~9k words), 1 long (2h audio ~18k words), and 1 cross-file series (2nd file with existing bible). Verify outputs against Quality Bar (brainstorm §9 + plan.md post-research criteria). Fix any spec deviations before Phase 6 docs.

## Context Links

- Plan Quality Bar (`plan.md` → Quality Bar section)
- Brainstorm §9 (acceptance criteria)
- Phase 4 prompt files (subject under test)
- Phase 2 scripts (subject under test)

## Requirements

**Functional:**
- Workflow runs end-to-end on 4 test scenarios without manual intervention
- Output files (`_image_prompts.txt`, `_video_prompts.txt`) are paste-ready into Gemini/Veo3
- Resume cache works: kill workflow mid-run, restart, only missing scenes regenerated
- Cross-file series: 2nd file uses existing bible without duplicating characters
- Override flags (`--images N`, `--videos M`, `--genre <name>`, `--force-redo`) all work
- đam mỹ sample correctly refused

**Non-functional (revised per red-team #4 — original budgets understated LLM latency):**
- Short file (2k words): <5 min wall time (~10 scenes × ~10s LLM call + overhead)
- Medium file (9k words): <25 min wall time (~50 scenes × ~10s + bible/plan/genre passes)
- Long file (18k words): <50 min wall time (~100 scenes × ~10s)
- Resume after kill: <30s overhead vs fresh run (skip cache-valid scenes)
- If budgets blow: redesign Pass 2 in Phase 4 to batch 5 scenes per LLM turn (deferred decision — see Risk Assessment)

## Architecture

```
plans/test-fixtures/
├── short-sample.txt           # 1 chapter, ~2k words, xianxia
├── medium-sample.txt          # 5 chapters, ~9k words, xianxia (Tru Tiên-style)
├── long-sample.txt            # 10 chapters, ~18k words, võ hiệp
├── series-file-1.txt          # 1st file of 2-file series (writes bible)
├── series-file-2.txt          # 2nd file (reads + augments bible)
└── danmei-sample.txt          # đam mỹ test (must be refused)

plans/260522-2230-visual-prompt-skill-implementation/test-results/
├── run-01-short.md            # Test log: timing, output diffs, quality bar checklist
├── run-02-medium.md
├── run-03-long.md
├── run-04-series.md
├── run-05-resume.md
└── run-06-overrides.md
```

## Related Code Files

### Create
- `plans/test-fixtures/short-sample.txt` — single xianxia chapter ~2k words (can source from existing proofreader test data or write a synthetic)
- `plans/test-fixtures/medium-sample.txt` — 5-chapter xianxia ~9k words
- `plans/test-fixtures/long-sample.txt` — 10-chapter võ hiệp ~18k words (test different genre too)
- `plans/test-fixtures/series-file-1.txt` + `series-file-2.txt` — same series, sequential chapters
- `plans/test-fixtures/danmei-sample.txt` — 1 chapter with đam mỹ keywords (verify refusal)
- 6 test result logs (one per test scenario)

### Modify
- Any prompt file from Phase 4 if test reveals spec deviation (e.g., LLM not citing Crouching Tiger → tighten instruction)
- Any reference file from Phase 3 if vocabulary gap found

### Delete
- (none)

## Implementation Steps

1. **Prepare test fixtures**:
   - Source short/medium/long samples from existing proofreader test data if available; else write/borrow 3 short xianxia excerpts
   - Series files: split a known novel's chapters 1-5 into file-1, chapters 6-10 into file-2
   - đam mỹ sample: 1 short scene with explicit BL romance keywords
2. **Run Test 01 (short, 2k words)**:
   - `cd plans/test-fixtures && /visual-prompt short-sample.txt`
   - Time wall clock; capture stdout to log
   - Verify outputs: `short-sample_image_prompts.txt` + `short-sample_video_prompts.txt` exist
   - Quality bar checks: ~10 images, ~2 videos, all on-spec (word count, format, identity anchor, Crouching Tiger ref, negatives 3-layer)
3. **Run Test 02 (medium, 9k words)**:
   - Same as above but with medium file
   - Quality bar: ~45 images, ~6 videos
   - Manual scan for 5 random scenes: format compliance + uniqueness
4. **Run Test 03 (long, 18k words, võ hiệp)**:
   - Test different genre (võ hiệp not xianxia) → verify genre detection + appropriate cinema ref (Hero not Crouching Tiger), no xianxia-specific keywords (no "tu tiên" terminology)
   - Quality bar: ~90 images, ~13 videos
5. **Run Test 04 (cross-file series)**:
   - `/visual-prompt series-file-1.txt --series tru-tien-test` → creates `~/.gemini/bibles/tru-tien-test.md`
   - `/visual-prompt series-file-2.txt --series tru-tien-test` → MUST reuse bible, MUST NOT duplicate Trương Tiểu Phàm character row
   - Diff bible after file-1 vs after file-2: only new characters appended; existing rows byte-identical
6. **Run Test 05 (resume after kill)**:
   - Start `/visual-prompt medium-sample.txt`
   - Kill (Ctrl+C) at ~30% scene expansion
   - Restart same command (no `--force-redo`)
   - Verify: completed scene files reused (no LLM call); only missing scenes regenerated
   - Total time: fresh-time × 0.7 (estimated savings)
7. **Run Test 06 (override flags)**:
   - `/visual-prompt short-sample.txt --images 5 --videos 1` → exactly 5 images, 1 video output
   - `/visual-prompt short-sample.txt --genre vo-hiep` → forced võ hiệp even if detector says xianxia
   - `/visual-prompt short-sample.txt --force-redo` after Test 01 → all scenes regenerated (verify timestamps changed)
8. **Run đam mỹ refusal test**:
   - `/visual-prompt danmei-sample.txt` → MUST halt with Vietnamese refusal message; MUST NOT write any output files
9. **Capture results in test log files**: timing, quality bar checklist per test, any spec deviations + fixes applied
10. **Fix any spec deviations**: tighten prompts/references; re-run failed test scenarios
11. **Final quality bar audit** across all 6 test outputs

## Todo List

- [ ] Test fixtures prepared (short, medium, long, 2 series, đam mỹ)
- [ ] Test 01 (short) passed quality bar
- [ ] Test 02 (medium) passed quality bar
- [ ] Test 03 (long, võ hiệp) passed quality bar — verifies non-xianxia genre path
- [ ] Test 04 (cross-file series) passed — bible byte-identical for existing chars
- [ ] Test 05 (resume) passed — kill+restart skips cached scenes
- [ ] Test 06 (overrides) passed — all 5 flags wired correctly
- [ ] đam mỹ refusal test passed — no output, Vietnamese message
- [ ] All spec deviations fixed; re-run scenarios green

## Success Criteria

- [ ] All 4 main scenarios + 2 edge cases (resume, refusal) green
- [ ] Wall times within budget (5/25/50 min for short/medium/long)
- [ ] Resume cache correctly detects stale state: manually edit input.txt after partial run → re-run flags affected scenes as stale (WARN message) and regenerates them
- [ ] Bible byte-identity verified via `diff` after cross-file series test (existing rows unchanged)
- [ ] Flag parse echo confirms parsed values match user input on Test 06; unknown flag (`--bogus`) halts with VN error
- [ ] Quality bar 100% on all output files:
  - Image prompts: 200-300 words sectioned, identity anchor verbatim, 3-layer negatives, cinema ref cited for xianxia/võ hiệp
  - Video prompts: Google 5-part, ms-timestamps `[00:00-00:02.5]`, audio as scene layer
  - Scene uniqueness: 0 pairs within 5 indexes with >70% overlap
- [ ] Cross-file series: bible existing rows byte-identical (diff = 0)
- [ ] Resume: 2nd run of partial workflow ≤30% wall time of full run
- [ ] đam mỹ sample halted; 0 output files written

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Test fixtures hard to source (proprietary novels) | Use proofreader's existing test data; else synthesize 3 short excerpts (1k each) |
| LLM nondeterminism makes outputs vary across runs | Quality bar checks structure not exact text; reruns must all pass spec, not produce identical output |
| Resume cache parses corrupted scene file | Phase 2 `assemble_outputs.py` logs WARNING + skips; resume re-runs that specific scene |
| Genre detection wrong on borderline (xianxia/võ hiệp mix) | `--genre` override flag available; test 06 verifies override path |
| Bible drift across files (rare LLM disobedience) | `.work/bible-conflicts.md` log; manual review in Test 04; tighten `bible-augmenter.md` if seen |
| Long file (18k words) exceeds LLM context per step | Workflow already pages: scene-planner loads chapters JSON summary not full text; expander loads only relevant chapter excerpt per scene |

## Security Considerations

- Test fixtures: ensure no copyrighted novel pasted publicly; keep in local `plans/test-fixtures/` (already .gitignore-able)
- đam mỹ refusal test confirms genre block working before any user-facing release

## Next Steps

- **Unlocks:** Phase 6 (docs can confidently document actual behavior)
- **Verification needed:** Phase 6 includes troubleshooting guide based on issues found here
