---
phase: 3
title: "Plan Gate Synopsis Dedup"
status: completed
effort: "S"
---

# Phase 3: Plan Gate Synopsis Dedup

## Overview
Extend `validate_scene_plan.py` with `duplicate_synopsis` — pairwise synopsis
similarity across the WHOLE plan (any distance). Kills stride-N plan copy
(chap16's +11 stride evaded WINDOW=10 tag+char check) BEFORE quota is spent
expanding duplicate rows.

## Related Code Files
- Modify: `scripts/validate_scene_plan.py`

## Implementation Steps
1. New check `check_synopsis_duplicates(rows)`: all pairs (i<j), difflib
   SequenceMatcher on synopsis strings, `quick_ratio()` prefilter, flag
   ratio ≥0.8 → `{'type': 'duplicate_synopsis', 'scene_ids': [a, b],
   'reason': 'synopsis {ratio:.0%} similar to scene {a} — rewrite this beat
   with a different moment/angle'}`.
2. Keep existing windowed tag+char check + fragment + diversity checks untouched.
3. Wire into `validate()` violation list.
4. Fixture test: synthetic 30-row plan with rows repeated at stride 11 →
   flagged; clean plan → ok.

## Success Criteria
- [x] Stride-11 fixture flagged as duplicate_synopsis
- [x] Clean plan unaffected (no new false positives on legit recurring chars/tags)
- [x] py_compile clean

## Risk Assessment
150 rows = ~11k pairs of short strings — trivial runtime. Threshold 0.8 on
synopses is conservative; scene_ids populated → STEP 5.5 revise loop targets
exact rows (TOML wiring in Phase 5).
