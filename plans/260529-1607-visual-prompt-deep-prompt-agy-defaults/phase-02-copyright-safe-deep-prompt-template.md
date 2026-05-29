---
phase: 2
title: Copyright-Safe Deep Prompt Template
status: completed
priority: P1
effort: 4-6h
dependencies:
  - 1
---

# Phase 2: Copyright-Safe Deep Prompt Template

## Context Links

- Code: `references/visual-prompt-template.md`
- Code: `references/style-catalog.md`
- Code: `references/negative-lists.md`
- Template: `.../template/binh-thien-sach-master-prompt-final.md`
- Research: `research/researcher-copyright-safety-and-agy.md`

## Overview

Rewrite the master prompt format so every image/video output is detailed,
layered, and original. Use the Bình Thiên Sách master template as structural
inspiration, not as copied content for every story.

## Requirements

- Functional: image prompts must include deep sections beyond the current basic six.
- Functional: video prompts must preserve the current 5-part formula but add depth requirements.
- Functional: prompt instructions must ban copying web images and famous/named faces.
- Functional: style catalog must stop requiring generated prompts to cite named IP/artist anchors.
- Non-functional: keep style ids stable to avoid breaking `--style <id>`.
- Non-functional: avoid legal claims; write operational prompt-safety constraints.

## Architecture

Add a reusable "Deep Prompt DNA" contract to `visual-prompt-template.md`:

- Story DNA: setting, era, faction pressure, cultivation/martial logic.
- Identity lock: character anchor, silhouette, costume, weapon, power signature.
- Scene composition: foreground/midground/background, scale, supporting actors.
- Environment layers: sky/weather, architecture/map, terrain, particles, aftermath.
- Camera/lens/framing: shot type, focal length, angle, motion if video.
- Lighting/palette: key/fill/rim, color DNA, shadow rule.
- Action/energy: combat beat, spell geometry, impact, debris, body mechanics.
- Audio for video/music: diegetic, ambient, instrumental-only where relevant.
- Negative/safety: no text/watermark, no famous likeness, no copied web image.
- Self-check: reject if shallow, generic, solo-only, or unsafe.

For `style-catalog.md`, keep the 18 ids but convert generated style blocks to
descriptive vocabulary. Historical/public-domain cultural movements are fine as
context; named living artists, commercial game/anime/film/IP likeness directives
should not appear in paste-ready prompt text.

## Related Code Files

- Modify: `references/visual-prompt-template.md`
- Modify: `references/style-catalog.md`
- Modify: `references/negative-lists.md`
- Modify: `prompts/prompt-expander-image.md`
- Modify: `prompts/prompt-expander-video.md`
- Modify: `prompts/style-recommender.md`
- Create: none
- Delete: none

## Implementation Steps

1. Add a "Deep Prompt DNA" section to `visual-prompt-template.md`.
2. Raise image target from current 200-300 words to a practical deep range, recommended 350-550 words with hard cap 650.
3. Keep video 5-part structure, but require richer detail inside each section; recommended 500-850 words with hard cap 900.
4. Add explicit safety rules: no copied web image, no celebrity/famous-character face, no living-artist style mimicry, no exact branded/IP likeness.
5. Rewrite paste-ready `Style block` fields in `style-catalog.md` to avoid named IP/artist phrasing while preserving stable ids.
6. Update `style-recommender.md` to recommend by original style descriptors, not reference anchors.
7. Update negative lists with likeness/copyright guard terms.
8. Keep examples synthetic and original; do not copy the Bình Thiên Sách text verbatim except as an external structural reference in docs.

## Success Criteria

- [ ] Generated prompt instructions require detailed multi-layer scene construction.
- [ ] No paste-ready style block asks for `in the style of <artist/IP/movie/game>`.
- [ ] Safety rules explicitly ban copying web images and famous faces.
- [ ] Style ids remain unchanged.
- [ ] Examples remain original and do not depend on external copyrighted characters.
- [ ] Image/video prompt self-checks fail shallow prompts.

## Risk Assessment

- Risk: removing named anchors weakens style steering.
  Mitigation: replace them with concrete visual descriptors: rendering medium, palette, line quality, material, lighting, camera language.
- Risk: long prompts become bloated.
  Mitigation: require specific details only; ban filler like "ultra detailed" repeated without scene information.
- Risk: style catalog rewrite is broad.
  Mitigation: keep ids/schema; edit content only.
