---
phase: 1
title: "Scene-Planner Content-Aware Diversity + Synopsis Fix"
status: completed
priority: P1
effort: "3-4h"
dependencies: []
---

# Phase 1: Scene-Planner Content-Aware Diversity + Synopsis Fix

## Overview

Replace v0.4's hard global action quota with content-aware targets, source
anti-monotony from visual variety (not fabricated combat), and fix the
synopsis-fragment bug so the planner emits coherent 1-line scene descriptions.

## Requirements

- Functional: `calc_scene_count.py` emits `action_density` (low/medium/high) +
  recommended scene-mix band, derived from a cheap keyword scan (no LLM pass).
- Functional: `scene-planner.md` consumes density → sets realistic mix; talky
  stories get low action target and draw variety from camera/scale/group/insert.
- Functional: planner synopsis is a coherent 1-line scene description, never a
  sliced text fragment.
- Functional: v0.4 combat/map/daoist-magic vocab + tags remain available for
  scenes/stories that genuinely have action.
- Non-functional: density scan must be O(text) keyword count, deterministic.

## Architecture

- **Density signal (deterministic):** extend `compute()` in `calc_scene_count.py`
  to scan chapter text for combat/action vocabulary (reuse/extend the keyword set
  used in brainstorm verify: kiếm, giao chiến, trận pháp, đại quân, chém, phi
  kiếm, công kích, huyết chiến, …). Emit `action_density` by hits-per-1k-words
  thresholds + a `recommended_mix` band:
  Thresholds (validated Session 1): **low `<2`, medium `2-6`, high `>6`** combat-hits/1k words.
  - low (talky): action 5-15%, establishing/map 25-35%, group/multi-char 20-30%,
    dialogue/emotional remainder.
  - medium: action 20-30%, establishing/map 25-35%, group 15-25%, remainder.
  - high: action 35-45% (the v0.4 band — now conditional, not default).
  <!-- Updated: Validation Session 1 - density low<2/med2-6/high>6 hits/1k; sample tmp_work5 ~0.13 -> low -->
- **Planner consumption:** `scene-planner.md` reads density + band from STEP 4
  output, replaces the hardcoded "35-45%" table with the content-aware band, and
  adds a VISUAL-VARIETY rule block: vary shot scale, include group tableaus of
  characters actually present, object/detail inserts for named props, flashback/
  symbolic shots, weather/time-of-day shifts — explicitly forbidding invented
  combat/armies absent from the chapter.
- **Synopsis fix:** add explicit rule — synopsis = one grammatical sentence
  describing WHAT is visually happening, drawn from the chapter meaning, NOT a
  copied substring. Add a self-check: reject synopsis that starts mid-word or is
  a raw text slice.

## Related Code Files

- Modify: `scripts/calc_scene_count.py` (add density + recommended_mix to JSON)
- Modify: `prompts/scene-planner.md` (content-aware band, visual-variety rule, synopsis rule + self-check)
- Modify: `commands/visual-prompt.toml` (STEP 4 prints density; pass band to planner in STEP 5)
- Modify: `references/scene-tag-camera-mapping.md` (only if a visual-variety note is needed; prefer no change)

## Implementation Steps

1. Add a small keyword set + `action_density`/`recommended_mix` computation to
   `calc_scene_count.py`; keep existing `images/videos/source` keys unchanged
   (additive only, so callers don't break).
2. Smoke-test the script on `tmp_work5/chapters_qa.json` (expect `low`) and a
   synthetic combat-heavy fixture (expect `high`).
3. Rewrite the scene-planner mix table to consume `recommended_mix`; remove the
   unconditional "35-45% action" default.
4. Add the VISUAL-VARIETY rule block with explicit no-fabrication guard.
5. Add synopsis-quality rule + self-check (no fragments / no raw slices).
6. Update `visual-prompt.toml` STEP 4 to print density and STEP 5 to feed the
   band into the planner prompt context.

## Success Criteria

- [ ] `calc_scene_count.py` JSON includes `action_density` + `recommended_mix`, old keys intact.
- [ ] Talky input yields `low` density and a low action band.
- [ ] Scene-planner no longer hardcodes 35-45% action as the default.
- [ ] Planner instructions require coherent synopsis + forbid fabricated combat.
- [ ] v0.4 combat tags/vocab still selectable when chapters support them.

## Risk Assessment

- Risk: keyword scan misclassifies a stylized action story as talky.
  Mitigation: thresholds tuned on real sample; `--epic` (Phase 4) overrides; band is a target not a hard cap.
- Risk: additive JSON keys break a strict consumer.
  Mitigation: only the toml/planner consume it; keep keys additive.
