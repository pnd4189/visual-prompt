---
phase: 4
title: Expander Quality Gates and Music Detail
status: completed
priority: P1
effort: 4-6h
dependencies:
  - 2
  - 3
---

# Phase 4: Expander Quality Gates and Music Detail

## Context Links

- Code: `prompts/prompt-expander-image.md`
- Code: `prompts/prompt-expander-video.md`
- Code: `prompts/music-prompt-builder.md`
- Code: `references/music-mood-mapping.md`

## Overview

Make the expanders enforce the deep prompt contract at write time. Music keeps
the current loop-count behavior, but each prompt becomes more specific and less
generic.

## Requirements

- Functional: image expander rejects shallow prompts.
- Functional: video expander includes motion, combat/energy detail, map scale, and audio when relevant.
- Functional: music builder keeps adaptive 3-5/default 4 and `--music N` override behavior.
- Functional: music prompt bodies become richer in instrumentation, emotional arc, dynamics, and production notes.
- Non-functional: no new output file; no new model/tool dependency.

## Architecture

Image expander should produce sectioned prompts with deeper fields:

```text
Camera:
Story DNA:
Setting:
Composition:
Subject:
Action / Energy:
Style:
Lighting / Color:
Atmosphere:
Negative:
```

Video expander keeps current headers for compatibility:

```text
Cinematography:
Subject:
Action:
Context:
Style & Ambiance:
```

Depth is added inside those headers, not by changing the output parser.

Music builder keeps output labels and instrumental-negative lines, but each loop
must specify genre register, mood transition, instrumentation layers, tempo/key,
dynamics, percussion, texture, mix/space, loop behavior, and vocal exclusion.

## Related Code Files

- Modify: `prompts/prompt-expander-image.md`
- Modify: `prompts/prompt-expander-video.md`
- Modify: `prompts/music-prompt-builder.md`
- Modify: `references/music-mood-mapping.md`
- Modify: `references/visual-prompt-template.md`
- Create: none
- Delete: none

## Implementation Steps

1. Update image expander task list to require all deep sections and scene-specific detail.
2. Add self-check: fail if prompt has fewer than 3 environment layers, lacks foreground/midground/background, or focuses only on one character when scene supports more.
3. Update video expander self-check: fail if action beats are generic, lack physical motion, or have no clear camera movement.
4. Add combat/daoist-magic guidance: spell geometry, weapon arc, impact, debris, terrain damage, crowd reaction.
5. Update music prompt builder: increase body specificity while preserving `Instrumental.`, `Negative:`, and `Loop:` contract.
6. Confirm `assemble_outputs.py` does not need parser changes; it extracts everything under existing headers.
7. Add explicit anti-filler rule: no generic quality word pile without concrete visual/audio facts.

## Success Criteria

- [ ] Image prompt instructions require deep section set and self-checks.
- [ ] Video prompt instructions preserve existing parser headers.
- [ ] Music prompt instructions keep current loop count behavior.
- [ ] Music prompt bodies include instrumentation layers and dynamics, not only mood words.
- [ ] Expander rules mention action, multi-character framing, and wide maps.
- [ ] No parser change is required in `assemble_outputs.py`.

## Risk Assessment

- Risk: adding image headers may break user paste expectations.
  Mitigation: output parser captures the whole image body; docs can explain the richer section format.
- Risk: video prompt too long for some tools.
  Mitigation: hard cap remains, and trim order is Context first, then Style detail.
- Risk: music prompt becomes lyrical/vocal.
  Mitigation: keep instrumental-only hard rule and vocal-negative line unchanged.
