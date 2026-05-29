---
phase: 3
title: "Assembly-Level Depth Gate + Auto-Regenerate"
status: completed
priority: P1
effort: "3-4h"
dependencies: [1]
---

# Phase 3: Assembly-Level Depth Gate + Auto-Regenerate

## Overview

Deterministic depth check at assembly: each image block must have all 10 section
headers, word count in range, and a sufficient negative list. Failing scenes are
deleted and regenerated via the expander, then re-assembled — capped retries.

## Requirements

- Functional: `assemble_outputs.py` emits a per-scene `violations` list in its
  JSON without changing the existing output `.txt` format.
- Functional: image-block checks — all 10 headers present
  (`Camera/Story DNA/Setting/Composition/Subject/Action / Energy/Style/Lighting / Color/Atmosphere/Negative`),
  body word count 350-650, negative item count **>= 20** (layers 1+3+4
  always-include = 19; floor 20 catches truncation without false positives).
  <!-- Updated: Validation Session 1 - negative floor 14 -> 20 -->
- Functional: video-block checks (for scenes with video) — 5 headers present,
  action has 2-3 timestamped beats, and **block length <= 3800 characters**
  (Google Flow / Veo3 hard-rejects prompts over 4000 chars; 3800 leaves margin).
  The char cap REPLACES the old 900-word cap as the binding limit.
- Functional: orchestrator deletes `.work/scene-NNN.md` for violating scenes,
  re-runs the expander(s) for them, re-assembles; capped at max retries.
- Functional: `prompt-expander-video.md` + `references/visual-prompt-template.md`
  (video section) replace the "500-850 words, hard cap 900" target with a
  character budget: target ~400-600 words, **HARD CAP 3800 chars**, with a
  char-count self-check before write and an explicit trim order (Context first,
  then Style detail, never drop a beat or the anchor).
- Non-functional: no new output file; checks are additive to assemble JSON.
  Expander + gate must use the SAME 3800 constant (DRY).

## Architecture

- **Extend `assemble_outputs.py`:** during `parse_scene`, run a `check_image`
  / `check_video` validator on the captured block text. Collect
  `violations: [{scene_id, kind, detail}]`. assemble still writes the `.txt`
  files (so a final-failure run is still usable) but reports violations in JSON.
  Keep `--- SCENE NNN ---` format and parser regexes unchanged.
- **Orchestration (toml STEP 7 loop):** after assemble, if `violations`
  non-empty AND retries remain → for each violating scene_id: delete
  `.work/scene-NNN.md`, re-run STEP 6 expander (image; video if flagged),
  re-run assemble. Cap at 2 retries. On final failure: WARN listing residual
  violations, keep the best output, proceed to summary.
- Word-count uses the same definition the expander self-check uses (body words,
  excluding section labels) to avoid mismatch between gate and generator.

## Related Code Files

- Modify: `scripts/assemble_outputs.py` (add `check_image`/`check_video`, `violations` in JSON; video char cap 3800)
- Modify: `commands/visual-prompt.toml` (STEP 7 becomes assemble → validate → bounded regen loop)
- Modify: `prompts/prompt-expander-video.md` (replace 900-word cap with 3800-char budget + char self-check + trim order)
- Modify: `references/visual-prompt-template.md` (video section: same char budget)

## Implementation Steps

1. Add header-presence + word-count + negative-count checks for image blocks.
2. Add 5-header + char-cap (<=3800) + beat-count checks for video blocks; define
   a shared `VIDEO_CHAR_CAP = 3800` constant and update `prompt-expander-video.md`
   + `visual-prompt-template.md` video section to the same budget + char self-check.
3. Add `violations` to the `assemble()` return dict and `main()` JSON output;
   keep `.txt` writing behavior unchanged.
4. Smoke-test: a shallow synthetic `scene-*.md` triggers violations; a rich one
   passes clean.
5. Rewrite toml STEP 7 into assemble → check → regen-flagged → re-assemble loop,
   capped at 2 retries, with a clear final WARN path.
6. Confirm video-index gaps + music assembly behavior are untouched.

## Success Criteria

- [ ] assemble JSON includes `violations`; `.txt` format byte-compatible with v0.4.
- [ ] Shallow block (missing header or <350 words) is flagged; rich block passes.
- [ ] Video block over 3800 chars is flagged; expander self-check trims before write.
- [ ] toml regenerates only violating scenes and re-assembles, capped.
- [ ] Final-failure path warns and still produces usable files.
- [ ] Word-count rule matches the expander self-check definition.

## Risk Assessment

- Risk: regen loop thrashes on a genuinely hard scene.
  Mitigation: max 2 retries, then warn-and-proceed; never infinite.
- Risk: negative-count floor conflicts with the 28-item cap logic.
  Mitigation: floor < cap (20 <= n <= 28); only flag below floor 20.
- Risk: parser change accidentally breaks `--- SCENE NNN ---` output.
  Mitigation: checks are read-only over parsed text; do not touch `_join`.
