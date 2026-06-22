---
phase: 3
title: "Wiring contract and versioning"
status: completed
priority: P1
dependencies: [1]
effort: ""
---

# Phase 3: Wiring contract and versioning

## Overview
Wire the Phase-1 gate into every run path (single-run TOML + batch driver), make
content-safety a first-class execution-contract rule, bump version in both
manifests, then run an end-to-end smoke. Depends on Phase 1 (script must exist).

## Requirements
- Functional: gate runs `--fix` after assemble in single-run (STEP 7) and batch
  (`run-folder.sh`); STEP 8 self-audit re-runs without `--fix` → PASS/WARN; a
  RULE documents the policy; version synced to 0.9.0.
- Non-functional: do not break existing gate ordering; gate failure must WARN, not
  hard-crash the batch; respect RULE 0 (no external model).

## Architecture
- TOML STEP 7: after `assemble_outputs.py` + depth gate, add gate call with
  `--fix` on `_image_prompts.txt` and (if videos) `_video_prompts.txt`.
- TOML STEP 8: re-run gate WITHOUT `--fix`; exit 0 → `Content-safety: PASS`,
  exit 2 → `Content-safety: WARN <residual>` (do not fail the run; surface in
  POST-RUN SUMMARY warnings).
- TOML EXECUTION CONTRACT: add a short RULE (content-safety) near RULE 0 — outputs
  must avoid the 8 categories; the gate enforces it; do not hand-edit outputs to
  bypass.
- `run-folder.sh`: in the existing for-loop (~L183-187, beside anchor gate), add
  `check_content_safety.py --blocklist "$SKILL_DIR/references/blocklist-content-safety.md" --output "$pf" --fix`.

## Related Code Files
- Modify: `commands/visual-prompt.toml` — STEP 7 add gate; STEP 8 re-run + report;
  add content-safety RULE; mention new files in any file-layout note.
- Modify: `scripts/run-folder.sh` — add gate call in the image/video loop.
- Modify: `SKILL.md` — Philosophy bullet for content-safety (8 categories incl.
  video animation-only); File Layout counts (9→10 references, 7→8 scripts —
  `references/` currently has 9 files, verified); `version: 0.9.0`; description
  mentions policy-safe.
- Modify: `gemini-extension.json` — sync `version` 0.9.0 + description (memory:
  version bump in two places; Agy reads the manifest).

## Implementation Steps
1. Edit TOML STEP 7: add the `--fix` gate call (image always; video if
   `video_count > 0`), parse exit code, keep depth-gate flow intact.
2. Edit TOML STEP 8: re-run gate without `--fix`; map exit 0/2 to PASS/WARN; add
   the WARN into POST-RUN SUMMARY warnings list.
3. Edit TOML EXECUTION CONTRACT: add the content-safety RULE.
4. Edit `run-folder.sh`: add the gate beside the anchor gate (image+video).
5. Bump `SKILL.md` (version + description + philosophy + file-layout counts) and
   `gemini-extension.json` (version + description) to 0.9.0, kept in sync.
6. End-to-end smoke: run on one small chapter `.txt`; confirm 4 outputs produced,
   gate ran, and final re-scan reports PASS (or expected WARN only for religion
   test inputs).

## Success Criteria
- [ ] Single-run (TOML) executes the gate after assemble and reports PASS/WARN at
      STEP 8; run still completes (no hard crash on WARN).
- [ ] `run-folder.sh` runs the gate for image and video files in the loop.
- [ ] `grep version SKILL.md gemini-extension.json` both show 0.9.0; descriptions
      consistent.
- [ ] SKILL.md File Layout counts updated (10 references, 8 scripts).
- [ ] Smoke run on a small file: outputs exist, no blocklist hits in final files.

<!-- Updated: Validation Session 1 - fixed references count 8->9 to 9->10 (actual references/=9) -->


## Risk Assessment
- Gate wired before output considered final → ensure it runs AFTER assemble so it
  edits the real `.txt`, like the anchor gate.
- Version drift between manifests → step 5 updates both in the same change; verify
  with grep.
- TOML is large (624 lines) → surgical edits only at STEP 7/8 + contract; no
  reflow of unrelated steps.
