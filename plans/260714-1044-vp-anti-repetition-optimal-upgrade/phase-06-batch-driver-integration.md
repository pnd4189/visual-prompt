---
phase: 6
title: "Batch Driver Integration"
status: completed
effort: "M"
---

# Phase 6: Batch Driver Integration

## Overview
`run-folder.sh`: run similarity gate externally (model cannot bypass) + smart
retry — similarity-only failure re-runs WITHOUT `--force-redo` (resume cache,
in-pipeline STEP 7.3 rewrites only flagged scenes; ~95% cheaper than full redo).

## Related Code Files
- Modify: `scripts/run-folder.sh`

## Implementation Steps
1. After check_run_legit PASS, add:
   ```bash
   python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
     --image "${local_stem}_image_prompts.txt" \
     $( [ -s "${local_stem}_video_prompts.txt" ] && echo --video "${local_stem}_video_prompts.txt" )
   sim_img=$?
   python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
     --music "${local_stem}_music_prompts.txt"   # khi file tồn tại
   ```
2. Retry differentiation in the 3-attempt loop (replace blanket --force-redo):
   - legit gate FAIL / missing image output → next attempt `--force-redo` (như cũ).
   - ONLY similarity exit 2 → next attempt WITHOUT `--force-redo` (plain re-run;
     pipeline resumes cache, STEP 7.3 targets flagged scenes).
   - 3 attempts exhausted → die (reject, không ship).
   - Similarity warnings (exit 0) → log dòng tóm tắt, proceed.
3. Keep gate order: legit → similarity → anchor consistency --fix →
   content-safety --fix → copy back.
4. `bash -n` + VP_DRYRUN=1 smoke.

## Success Criteria
- [x] bash -n clean; dry-run shows expected flow
- [x] Similarity-only fail path re-runs without --force-redo
- [x] Reject path preserves die-with-resume-hint behavior

## Risk Assessment
Plain re-run attempt inherits cached scenes — correct by design (STEP 7.3 gate
re-fires on resume because assemble+check re-run). Nếu model không sửa nổi sau
3 attempts → reject là hành vi đúng (không ship template).
