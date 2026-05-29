# Visual Prompt v0.4 — Deep Prompt Quality Plan

**Date**: 2026-05-29 16:07  
**Severity**: Medium  
**Component**: visual-prompt skill — Agy CLI command, prompt generation, scene planning  
**Status**: Implemented  

## What Happened

Created the v0.4 implementation plan for `/visual-prompt` after user clarified
new production requirements:

- Default output should be around 120-150 image prompts.
- Default video output should be at least 20 prompts.
- Final output remains four files.
- Agy CLI / Antigravity is the target runtime; Gemini CLI wording should be removed.
- Prompt quality must follow the deep Bình Thiên Sách master-template structure.
- Prompts must avoid copied web images, famous faces, celebrity likenesses, and
  named-character likeness copying.
- Scene planning must include more action, combat, daoist magic, wide maps, and
  multi-character frames.
- Music count stays as-is; only prompt detail should improve.

## Decisions

- Keep existing architecture. No new output files, no new dependencies.
- Centralize new default counts in `scripts/calc_scene_count.py`.
- Keep `--images`, `--videos`, and `--music` override semantics unchanged.
- Rewrite active prompt/style reference files, not historical reports.
- Treat style ids as stable; only rewrite unsafe paste-ready wording.

## Artifacts

- Plan: `plans/260529-1607-visual-prompt-deep-prompt-agy-defaults/plan.md`
- Research: `plans/260529-1607-visual-prompt-deep-prompt-agy-defaults/research/`
- Reports: `plans/260529-1607-visual-prompt-deep-prompt-agy-defaults/reports/`

## Implementation Result

- Updated default scene count to 120-150 images and 20+ videos.
- Raised image/video/music prompt depth requirements.
- Added action, combat, daoist magic, group, and map-scale planning rules.
- Rewrote style guidance to descriptive original vocabulary.
- Added likeness/copyright safety negatives.
- Fixed style-dependent music cache invalidation by including `style_hash`.
- Updated docs for Agy CLI and high-count defaults.

## Verification

- Python compile passed for touched/support scripts.
- TOML parse passed for `commands/visual-prompt.toml`.
- Count smoke passed: auto `120/20`, override `30/4`, mixed overrides exact.
- Static grep found no positive IP/artist imitation directives in active files.
- Tester agent: DONE.
- Reviewer agent: DONE_WITH_CONCERNS; all reported concerns were fixed.

## Next

Manual Agy run on a real Bình Thiên Sách input is still useful to judge creative
quality, repetition rate, and how strongly the active model follows the new
self-checks.
