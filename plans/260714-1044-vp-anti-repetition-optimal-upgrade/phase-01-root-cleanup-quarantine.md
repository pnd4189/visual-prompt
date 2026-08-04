---
phase: 1
title: "Root Cleanup Quarantine"
status: completed
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
- [x] Repo root clean (untracked = plans/ + quarantine only)
- [x] chap16 fixture path identified + recorded for Phase 7
- [x] Commit 1 landed

## Closure (2026-08-04, reconciled by plan 260729-1645 Phase 0)
- The original step-1 recipe ("move every untracked except plans/") was NOT
  re-run — it is stale; today's untracked includes legit `docs/journals/*`
  and `plans/**`. Final root cleanup executed as the targeted inventory
  quarantine `.quarantine-260804/` (see its `RESTORE.md`).
- chap16 fixture = `.quarantine-260713/local_chap16.txt` (kept in place;
  `.quarantine-260713/` untouched). Note: fixture is post-repair output —
  original failing state (38 Camera exact dups) lives only in
  `.quarantine-260713/full_report.md`.
- Commit 1 never landed as a standalone commit: quarantined items were
  untracked/gitignored, so the move needed no commit; recovery path is
  documented instead.

## Risk Assessment
Some .txt may be user inputs → quarantine (not delete) keeps them recoverable;
list reported to user at end.
