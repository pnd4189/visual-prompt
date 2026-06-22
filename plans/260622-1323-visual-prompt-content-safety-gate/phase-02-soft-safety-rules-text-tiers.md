---
phase: 2
title: "Soft safety rules (text tiers)"
status: completed
priority: P2
dependencies: []
effort: ""
---

# Phase 2: Soft safety rules (text tiers)

## Overview
Strengthen the prevention layer so the model rarely produces a violation in the
first place. Pure prompt/reference editing — no code. Covers all 8 categories
(#8 photoreal/live-action ban is video-scoped), keeps the spectacle rail and
genre-native religious imagery intact.

## Requirements
- Functional: every image/video prompt instruction + negative list explicitly
  bans naming brands/real people/IP in positive sections and depicting gore/
  sexual/anti-religion content; planner avoids planning such scenes.
- Non-functional: keep negative budget at exactly 28 items; do not break the
  depth gate (`negative ≥ 20`, word-count band); surgical edits, match file style.

## Architecture
Negative list re-budget (keep 28): Layer 1 10→8 (drop 2 least-critical Western
items, e.g. `no celtic knotwork, no crusader cross`), Layer 4 4→6 renamed
"Safety & Compliance":
```
no copied web image, no real public figure or celebrity face,
no copyrighted character likeness, no brand logo or trademark,
no nudity or suggestive exposure, no graphic gore or blood splatter
```
Religion is NOT a negative-list item (visual-negatives can't encode it) — handled
in expander/planner prose + hard gate.

## Related Code Files
- Modify: `references/negative-lists.md` — Layer 1 8 items, Layer 4 6 items
  "Safety & Compliance", update the composed 28-item example + count note.
- Modify: `prompts/prompt-expander-image.md` — turn step-7 + self-check step-4
  into a hard SAFETY rule block (no brand/real-person/IP names in ANY positive
  section; no nudity/sexual; combat OK but no graphic gore; respect real religion;
  abstract forbidden chapter content).
- Modify: `prompts/prompt-expander-video.md` — same SAFETY rule in its step-1
  intro + step-7 safety check, PLUS the #8 animation-only rule: video MUST render
  in the chosen animated/illustrated style; ABSOLUTELY no live-action, no
  photoreal footage, no real-human likeness (avoid AI-slop / inauthentic-content
  policy). Add inline video negatives (Style & Ambiance "avoiding ..."):
  `no live-action, no photorealistic footage, no real human face or skin,
  no deepfake realism`. Keep painterly "semi-realistic" styles allowed (the ban
  targets live-action realism, not the catalog's painterly styles).
- Modify: `prompts/scene-planner.md` — extend the existing copyright note (line
  ~95) into a planning rail: never plan a scene whose purpose is gore/sexual/
  anti-religion; abstract it; keep fictional cultivation imagery allowed.
- Modify: `references/visual-prompt-template.md` — expand "Originality and
  likeness safety" into "Safety & Compliance" listing all 8 categories + update
  the example Negative line to the new 6-item Layer 4.

## Implementation Steps
1. Edit `negative-lists.md`: trim Layer 1 to 8, rewrite Layer 4 (6 items, new
   title), fix the "Max 28 items (8+5+5+6+4)" math note, update Composed Example.
2. Edit `prompt-expander-image.md`: add explicit SAFETY rule + extend MANDATORY
   SELF-CHECK step 4 to cover categories 1-7 and the positive-section ban (#8
   photoreal/live-action goes in the video expander, step 3).
3. Edit `prompt-expander-video.md`: mirror the SAFETY rule + safety check + the
   #8 animation-only rule and inline video negatives.
4. Edit `scene-planner.md`: add the planning rail; keep spectacle + genre-native
   religion explicit so it isn't over-blocked.
5. Edit `visual-prompt-template.md`: rewrite safety section + example negative.

## Success Criteria
- [ ] `negative-lists.md` Composed Example has exactly 28 comma items; math note
      reads 8+5+5+6+4.
- [ ] Both expanders state: no brand/real-person/IP name in positive sections;
      no nudity/sexual; no graphic gore (combat allowed); respect real religion;
      abstract forbidden chapter content.
- [ ] scene-planner rail present and explicitly permits fictional cultivation/
      Daoist/Buddhist imagery (no over-block).
- [ ] template safety section lists all 8 categories; example negative matches the
      new Layer 4.
- [ ] video expander states animation-only (#8): no live-action / photoreal
      footage / real-human likeness; painterly styles still allowed.
- [ ] No change to combat/spectacle wording elsewhere.

<!-- Updated: Validation Session 1 - added #8 video animation-only rule to video expander -->


## Risk Assessment
- Dropping 2 Layer-1 items slightly weakens Western-drift guard → acceptable
  (xianxia genre + Layer 2 already cover it); revisit if drift observed.
- Over-blocking religion → mitigated by explicit "fictional cultivation allowed"
  carve-out in planner + expanders.
