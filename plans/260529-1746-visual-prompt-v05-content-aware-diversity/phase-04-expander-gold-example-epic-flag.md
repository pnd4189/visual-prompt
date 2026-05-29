---
phase: 4
title: "Expander Gold Example + Epic Flag"
status: completed
priority: P2
effort: "2-3h"
dependencies: [1]
---

# Phase 4: Expander Gold Example + Epic Flag

## Overview

Make the image expander explicitly reference + adhere to the gold-standard example
that ALREADY lives in `visual-prompt-template.md` (no duplicate copy — DRY), and
add an optional `--epic` flag that amplifies scale/spectacle when the user wants it
and the story genuinely supports it.

<!-- Updated: Validation Session 1 - template already has example; reference it, do not embed a duplicate -->

## Requirements

- Functional: verify the existing template example (`visual-prompt-template.md`
  ~lines 86-99) covers ALL 10 image sections at target depth with multi-character/
  layered framing. If a section is missing, augment the TEMPLATE example (single
  source), not the expander.
- Functional: `prompt-expander-image.md` adds an explicit rule: read the template
  example and match its structure + depth; reject shallow output that diverges.
- Functional: `--epic` flag, when set, raises the action/map/group target band
  one notch and tells the planner/expander to favor wide spectacle — but the
  no-fabrication rule still holds (amplify what exists, don't invent battles).
- Non-functional: no duplicated example text across files (DRY).

## Architecture

- **Gold example (reference, not embed):** the template is the single source of the
  example. Augment it only if it lacks a section. `prompt-expander-image.md` gets a
  one-line mandatory rule pointing at the template example as the depth/structure
  bar to match — no copied block.
- **`--epic` flag:** parse in toml STEP 0 (add to allowed-flag regex list);
  when set, bump the `recommended_mix` band one notch in calc/planner context and
  add an "epic mode" note to the planner + expander (wide establishing, larger
  group tableaus, grander scale cues). Document that it amplifies, never fabricates.

## Related Code Files

- Modify: `references/visual-prompt-template.md` (augment example only IF a section is missing)
- Modify: `prompts/prompt-expander-image.md` (add reference-and-adhere rule to template example)
- Modify: `commands/visual-prompt.toml` (STEP 0 flag parse `--epic`; thread into STEP 4/5)
- Modify: `prompts/scene-planner.md` (epic-mode note)
- Modify: `SKILL.md` (document `--epic` in Usage)

## Implementation Steps

1. Read the existing template example; confirm it has all 10 sections + multi-char
   depth. Augment the template ONLY for any missing section.
2. Add a mandatory "match the template example's structure + depth" rule to
   `prompt-expander-image.md` (reference, no duplicate block).
3. Add `--epic` to toml STEP 0 flag parser + the unknown-flag error list.
4. Thread `epic` into the density/band logic (one-notch bump) and add epic note
   to planner + expander prompts.
5. Update `SKILL.md` Usage line + flag list to include `--epic`.

## Success Criteria

- [ ] Template example confirmed/augmented to all 10 sections; no duplicate copy elsewhere.
- [ ] Image expander has an explicit rule to match the template example's depth.
- [ ] `--epic` parses without error and bumps the target band one notch.
- [ ] Epic mode still forbids fabricated combat/armies.
- [ ] SKILL.md documents `--epic`.

## Risk Assessment

- Risk: example and live spec drift apart over time.
  Mitigation: single source (template); expander references it, never copies.
- Risk: `--epic` reintroduces fabrication.
  Mitigation: keep the no-fabrication guard above the epic note; epic only amplifies existing beats.
