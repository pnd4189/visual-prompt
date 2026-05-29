---
phase: 3
title: Scene Diversity and Action Planning
status: completed
priority: P1
effort: 3-5h
dependencies:
  - 1
  - 2
---

# Phase 3: Scene Diversity and Action Planning

## Context Links

- Code: `prompts/scene-planner.md`
- Code: `references/scene-tag-camera-mapping.md`
- Code: `references/genre-keywords.md`
- Research: `research/researcher-prompt-depth-and-counts.md`

## Overview

Prevent 120-150 outputs from becoming repetitive main-character portraits.
Scene planning must deliberately allocate action, combat, daoist magic, group
composition, wide map shots, and multi-character frames.

## Requirements

- Functional: scene plan includes exact `images_n` and `videos_m`.
- Functional: video scenes prioritize motion-rich beats.
- Functional: planner must include multi-character and wide-map scenes when supported by the chapter.
- Functional: near-duplicate checks become stricter for high-count runs.
- Non-functional: no hallucinated named characters; supporting crowds/factions can be generic when chapter context allows.

## Architecture

Extend scene rows with planning hints if needed while preserving current table
shape where possible. Prefer adding fields only if expanders can consume them
reliably; otherwise encode details in `synopsis`.

Recommended scene mix for auto high-count runs:

| Category | Target |
|---|---|
| action/combat/ritual/reveal | 35-45% |
| wide environment/map/establishing | 20-30% |
| multi-character interaction/group | 15-25% |
| close-up/emotional/dialogue | remainder |

Video flag priority:
1. combat exchange / chase / impact
2. daoist magic / formation / breakthrough
3. large-scale reveal / map-scale traversal
4. crowd or army movement
5. opener/climax/resolution beats

## Related Code Files

- Modify: `prompts/scene-planner.md`
- Modify: `references/scene-tag-camera-mapping.md`
- Modify: `references/genre-keywords.md`
- Modify: `prompts/prompt-expander-image.md`
- Modify: `prompts/prompt-expander-video.md`
- Create: none
- Delete: none

## Implementation Steps

1. Add diversity targets and category mix rules to `scene-planner.md`.
2. Require the planner to extract factions/groups/locations from chapter text, not only named protagonists.
3. Add explicit anti-monotony rule: reject repeated "single character standing/gazing" scenes unless the story moment demands it.
4. Strengthen uniqueness self-check for high-count runs: compare within 10 indices, not only 5.
5. Update scene-tag/camera mapping with combat/map/group-oriented defaults.
6. Update genre keywords for battlefields, formations, sect crowds, armies, spiritual beasts, city-scale vistas, and daoist magic visuals.
7. Ensure video flagging selects at least 20 motion-rich scenes by default.

## Success Criteria

- [ ] Scene planner states the target category mix.
- [ ] Video-flag rule explicitly requires `videos_m` motion-rich scenes.
- [ ] Prompts can include supporting actors/crowds without inventing named characters.
- [ ] Wide map shots and combat scenes are first-class, not incidental.
- [ ] Duplicate check catches repeated solo portraits.

## Risk Assessment

- Risk: the model invents extra named characters.
  Mitigation: allow unnamed supporting groups only when chapter context supports them; named characters must come from bible/chapter.
- Risk: too much action distorts quiet chapters.
  Mitigation: targets are preferred mix for full run; quiet chapters can use wide map/ritual/reveal instead of fake combat.
- Risk: scene table gets too complex.
  Mitigation: prefer richer `synopsis` and existing tags before adding new columns.
