---
phase: 1
title: "Root Cleanup Quarantine"
status: in-progress
effort: "S"
---

# Phase 1: Root Cleanup Quarantine

## Overview
Quarantine 55 untracked scratch items polluting repo root (from manual audit
session: 14 root .py incl. generator.py/generate_prompts.py, test_*.py,
local_*/tmp files, .agents/, PROJECT.md, local_work/). Recoverable move, no delete.

## Related Code Files
- Create: `.quarantine-260713/` (gitignored via existing `.quarantine-*/` pattern)
- No source files modified.

## Implementation Steps
1. `git status --porcelain | grep '^??'` → move every untracked entry EXCEPT
   `plans/` and `.quarantine-*` into `.quarantine-260713/` (preserve relative
   path only for name collisions; flat move otherwise, same pattern as
   `.quarantine-260708/`).
2. KEEP a reference copy of `check_similarity.py` + `full_report.md` readable
   (they stay inside quarantine; Phase 2 reads from there — do NOT delete).
3. Locate the chap16 test corpus among quarantined `local_*`/`new_output*` files
   (the image-prompts file whose Camera exact-dup count = 38 per full_report.md);
   note its quarantine path for Phase 2/7 verification.
4. Verify: `git status --porcelain | grep '^??'` shows only `plans/` +
   quarantine dirs; `scripts/` still exactly 16 canonical files.
5. Commit 1: `chore: quarantine manual-session scratch from repo root`.

## Success Criteria
- [ ] Repo root clean (untracked = plans/ + quarantine only)
- [ ] chap16 fixture path identified + recorded for Phase 7
- [ ] Commit 1 landed

## Risk Assessment
Some .txt may be user inputs → quarantine (not delete) keeps them recoverable;
list reported to user at end.
