---
phase: 1
title: Default Counts and Agy Command Contract
status: completed
priority: P1
effort: 2-3h
dependencies: []
---

# Phase 1: Default Counts and Agy Command Contract

## Context Links

- Code: `scripts/calc_scene_count.py`
- Code: `commands/visual-prompt.toml`
- Docs: `SKILL.md`, `README.md`, `HUONG-DAN-SU-DUNG.md`
- Research: `research/researcher-prompt-depth-and-counts.md`

## Overview

Change the default production scale and make Agy CLI the only described runtime.
This phase should not touch prompt content quality yet; it establishes the count
and command contract the later phases rely on.

## Requirements

- Functional: no flag path generates about 120-150 image prompts.
- Functional: no flag path generates at least 20 video prompts.
- Functional: `--images N` and `--videos M` continue to override exactly as today.
- Functional: mixed overrides remain supported.
- Functional: command text says active Antigravity/Agy model drives the workflow.
- Non-functional: no new dependencies, no new output files, no new config file.

## Architecture

Keep `calc_scene_count.py` as the only count calculator. Recommended auto formula:

```python
auto_images = min(150, max(120, round(wordcount / 120)))
auto_videos = max(20, round(auto_images / 6))
```

This honors the user's "120-150 each run" requirement while still scaling long
inputs slightly. Overrides remain passthrough and may intentionally produce counts
outside the default range.

## Related Code Files

- Modify: `scripts/calc_scene_count.py`
- Modify: `commands/visual-prompt.toml`
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `HUONG-DAN-SU-DUNG.md`
- Create: none
- Delete: none

## Implementation Steps

1. Update `scripts/calc_scene_count.py` docstring and `compute()` auto formula.
2. Add focused tests or a small smoke command matrix for word counts and override cases.
3. Update `commands/visual-prompt.toml` STEP 0/4 wording: Agy CLI active model, not Gemini CLI.
4. Update post-run summary wording if it references Gemini as the runtime.
5. Update README/SKILL/guide usage sections to reflect 120-150 images, 20+ videos, and Agy CLI target.
6. Leave paste targets like image/video/music generation tools in docs only where useful; do not describe Gemini CLI as the runtime.

## Success Criteria

- [ ] Auto count for a small/normal input returns `images >= 120` and `videos >= 20`.
- [ ] Auto count for a long input returns `images <= 150`.
- [ ] `--images 30 --videos 4` still returns exactly 30 and 4.
- [ ] Mixed override behavior is unchanged and documented.
- [ ] Docs no longer say Gemini CLI is an equivalent runtime.
- [ ] No output filename contract changes.

## Risk Assessment

- Risk: 120 prompts for short input can cause duplicate scenes.
  Mitigation: Phase 3 scene diversity rules must require micro-moment splitting and duplicate checks.
- Risk: large count makes runs slower.
  Mitigation: docs warn about longer runtime; cache behavior remains unchanged.
- Risk: removing Gemini CLI wording could accidentally remove paste-target guidance.
  Mitigation: separate runtime wording from tool paste guidance.
