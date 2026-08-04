---
phase: 2
title: "Similarity Gate Script"
status: in-progress
effort: "L"
---

# Phase 2: Similarity Gate Script

## Overview
New canonical `scripts/check_prompt_similarity.py` — deterministic cross-scene
similarity gate (image/music/video) + visual-history extractor. Absorbs proven
difflib+tfidf logic from quarantined `check_similarity.py`, fixes its 2 parser
bugs, adds policy/exit-code contract matching sibling gates.

## Requirements
- Functional: detect copy-paste/near-verbatim reuse across scenes; emit
  machine-readable rewrite targets; maintain per-series visual-history.
- Non-functional: <30s on 150-scene file (quick_ratio prefilter); stdlib only.

## Architecture
Compared fields (image): Camera, Story DNA, Setting, Composition,
Action / Energy, Lighting / Color, Atmosphere. EXCLUDED by design (verbatim
legit): Subject, Style, Negative.

Parser: split on `^--- SCENE (\d+) ---$`; a line starts a field ONLY if it
matches one of the 10 known headers, plain `Camera:` or bold `**Camera:**`;
any other `Word:` line (Foreground:, Midground:...) = continuation of current
field. (Bug fixes vs original: bold labels + unknown-label continuation.)

Similarity: sim = max(difflib.SequenceMatcher.ratio, tfidf cosine); call
`quick_ratio()` first, skip full ratio when quick < soft threshold.

Policy (locked):
- VIOLATION → exit 2:
  - `pair_copy`: scene pair with ≥2 fields sim ≥ near (0.95); FAIL when
    count > --max-pair-copies (default 1).
  - `field_dup_flood`: one field with > --max-exact-per-field (default 4)
    pairs at sim ≥0.995.
- WARNING → exit 0: pairs in [soft 0.60, near 0.95).
- exit 1: IO error. Flags: `--soft 0.60 --near 0.95 --max-pair-copies 1
  --max-exact-per-field 4`.

Modes:
- `--image <file>`: as above.
- `--music <file>`: pairwise loop-body sim ≥0.75 = violation; identical first
  8 words of paragraph = violation; tag-set overlap >70% between two loops =
  warning. Parse `--- LOOP i / N ...---` separators.
- `--video <file>` (optional): pairwise body sim ≥ near = violation pair
  (plugs legit-gate hole: it only FAILs >50% identical).
- `--extract-history --image F [--music F] --history <path>`: distill Camera
  line, Setting first sentence (≤200 chars), Action/Energy motif first clause,
  music intro (first 8-10 words), music tags → append to history file sections
  (`## camera framings used`, `## settings used`, `## action motifs used`,
  `## music intros used`, `## music tags used`); dedupe; rolling cap 150
  lines/section (keep newest); create file if absent. Exit 0.

JSON stdout (check modes):
`{ok, violations:[{type, field?, scene_a, scene_b, sim}], warnings:[...],
stats:{per-field avg/max/exact/high}, rewrite_scene_ids:[...], banned_phrases:[...]}`
- rewrite_scene_ids: for each violation cluster keep LOWEST scene id, list the rest.
- banned_phrases: the duplicated field texts (truncated ~160 chars each, deduped).

## Related Code Files
- Create: `scripts/check_prompt_similarity.py`
- Modify: `scripts/check_run_legit.py` (add name to CANONICAL_SCRIPTS — MANDATORY,
  else purge gate quarantines the new script on next batch)

## Implementation Steps
1. Write script per architecture above (single file, argparse, stdlib).
2. Add to CANONICAL_SCRIPTS.
3. Smoke: run `--image` on chap16 fixture (path from Phase 1) → expect exit 2,
   Camera exact ≈38 pairs, plenty pair_copy violations.
4. Smoke: `--extract-history` twice on same file → idempotent (dedupe), cap holds.
5. `python3 -m py_compile` clean; `--purge-skill-dir .` reports 0 rogue.

## Success Criteria
- [ ] chap16 → FAIL with stats matching full_report.md (±: same exact counts)
- [x] A clean small fixture → exit 0 with only warnings/empty
- [x] extract-history idempotent + capped
- [x] Script survives purge gate (in allowlist)

## Risk Assessment
False-positive FAIL on short formulaic Camera lines → mitigated by pair_copy
needing ≥2 fields + count thresholds; flags allow tuning without code change.
