---
title: "Visual Prompt v0.9 — Content-Safety Gate"
description: "Hybrid soft-rules + deterministic gate so visual-prompt outputs never name brands/real people/IP, never depict excessive gore or sexual content, and never disrespect/distort real religion. Auto-strip + WARN."
status: completed
priority: P2
branch: "main"
tags: [visual-prompt, safety, copyright, content-policy]
blockedBy: []
blocks: []
created: "2026-06-22T06:40:55.128Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt v0.9 — Content-Safety Gate

## Overview

Add a supplementary safety mechanism to `/visual-prompt` so generated image/video
prompts avoid copyright + platform-policy + religious-sensitivity violations.
Hybrid design (decided in brainstorm report
`plans/reports/brainstorm-260622-1323-visual-prompt-content-safety-gate-report.md`):

- **Soft tier** — strengthen text rules across negative-lists, both expanders,
  scene-planner, template, SKILL.md, TOML (prevent at generation time).
- **Hard tier** — new deterministic gate `scripts/check_content_safety.py` +
  data file `references/blocklist-content-safety.md`, wired into TOML STEP 7/8
  and `run-folder.sh`, mirroring `check_anchor_consistency.py`.

**8 blocked categories:** (1) brand/logo/trademark, (2) real public figures /
faces, (3) copyrighted IP characters, (4) copyrighted images/artworks,
(5) excessive gore/violence, (6) sexual/nudity, (7) religious disrespect/
distortion, (8) photoreal/live-action VIDEO (animation-only — avoid AI-slop /
inauthentic-content policy).

**On-violation:** auto-strip offending span → generic, print WARN (does not halt
headless batch — incl. religion, which is WARN-and-ship). Religion category is
WARN-biased (regex cannot judge context; not auto-rewritten).

## Locked decisions (from brainstorm + planning)

- Spectacle rail kept: combat/đấu pháp allowed; only EXCESSIVE gore blocked
  (decapitation, disembowel, gushing blood, torture). Stylized/light-blood combat OK.
- Likeness regex fires ONLY with a trigger ("looks like / in the style of /
  cosplay / giống / theo phong cách / mô phỏng" + name) — never bare Proper-Noun
  scan → protects Hán-Việt character names.
- Religion: genre-native fictional Daoist/Buddhist cultivation imagery (tu tiên,
  đạo sĩ, chùa) is NOT blocked. Only blocks insulting/distorting/desecrating REAL
  religion (e.g. depicting real prophets/deities, sacred symbol + gore/nudity).
- Negative budget stays 28: Layer 1 10→8, Layer 4 4→6 → `8+5+5+6+4=28`.
  VERIFIED safe: `assemble_outputs.py:44` floor is always-include Layers 1+3+4 =
  19 items; new split `8+5+6=19` keeps the floor invariant, depth gate
  `NEGATIVE_MIN=20` not broken.
- Gate scans the assembled `_image_prompts.txt` / `_video_prompts.txt` (mirror
  anchor gate), `--fix` once. Fix edits the `.txt` ONLY (like anchor gate) —
  re-run from cached `scene-*.md` may re-surface a hit (accepted, same as anchor).
- Version bump 0.8.0 → 0.9.0 in BOTH `SKILL.md` and `gemini-extension.json`.
- Religion = WARN-and-ship (no HALT); brand/IP match = case-insensitive
  whole-word + curated list.
- Video animation-only (#8): video prompts must be the chosen animated/illustrated
  style; ban LIVE-ACTION / real-photo footage / real-human likeness. Detection
  must NOT match legit painterly style words ("semi-realistic", "photo-real
  lighting", "realistic textures") — only strong live-action/photoreal-footage
  signals.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Hard gate core (script + blocklist)](./phase-01-hard-gate-core-script-blocklist.md) | Completed |
| 2 | [Soft safety rules (text tiers)](./phase-02-soft-safety-rules-text-tiers.md) | Completed |
| 3 | [Wiring contract and versioning](./phase-03-wiring-contract-and-versioning.md) | Completed |

## Dependencies

- Phase 3 blockedBy Phase 1 (wiring needs the script to exist).
- Phase 2 independent (pure text), can run anytime.
- No cross-plan dependencies. Prior visual-prompt plans are implemented/completed;
  v0.5 "in-progress" is stale (skill already v0.8) and concerns diversity, not safety.

## Acceptance (whole plan)

- [ ] `check_content_safety.py --fix` on a crafted sample (brand + "looks like
      <real actor>" + gore + nudity) strips all to generic, exits 0 on re-scan.
- [ ] Same script does NOT alter a fictional Hán-Việt character name or a
      Daoist-temple cultivation scene (no false positive).
- [ ] Negative section still has exactly 28 items, depth gate (`negative ≥ 20`)
      stays green.
- [ ] TOML STEP 7 runs the gate with `--fix`; STEP 8 re-runs without `--fix` and
      reports PASS or WARN.
- [ ] `run-folder.sh` runs the gate alongside the anchor gate for image+video.
- [ ] Version reads 0.9.0 in SKILL.md and gemini-extension.json; descriptions synced.
- [ ] End-to-end smoke on one small chapter file produces outputs with no
      blocklist hits.
- [ ] Video expander bans live-action / photoreal-footage / real-human likeness;
      gate flags `live-action`/`photorealistic footage`/`real human actor` in the
      video file but does NOT strip `semi-realistic` / `photo-real lighting` from
      a legitimately-chosen painterly style.

## Out of scope

- No ML classifier; blocklist + regex only.
- Not exhaustive coverage of all world brands/IP/religions (curated, extensible).
- No change to combat/spectacle behaviour.
- Video #8 bans live-action/real-human realism, NOT the painterly "semi-realistic"
  art styles in the catalog.

## Validation Log

### Session 1 — 2026-06-22

**Verification Results (Standard tier, 3 phases)**
- Claims checked: ~12. Verified: 11 | Failed: 1 | Unverified: 0.
- VERIFIED: `check_anchor_consistency.py` shape/exit-codes; `run-folder.sh:185`
  image/video loop; `scene-planner.md:95-96` safety note; TOML STEP 7/8; negative
  re-budget keeps always-include 19 + total 28 (`assemble_outputs.py:44`,
  `NEGATIVE_MIN=20`).
- FAILED: phase-03 said references "8→9" — actual `references/` = 9 files, so
  correct is **9→10**. Corrected in phase-03 + this log.

**Decisions confirmed**
1. Religion violation → WARN-and-ship (no HALT, not auto-rewritten).
2. Brand/IP literal match → case-insensitive whole-word + curated list.
3. `--fix` edits assembled `.txt` only (mirror anchor gate); cached `scene-*.md`
   not rewritten (accepted limitation).
4. Fact-fix → references count 9→10.

**New requirement (#8 — video animation-only)**
- Video prompts must render in the chosen animated/illustrated style; ABSOLUTELY
  no live-action / real-photo footage / real-human likeness (avoid AI-slop +
  inauthentic-content policy). Propagated to Phase 1 (blocklist `PHOTOREAL_VIDEO`)
  + Phase 2 (video expander rule + inline negatives).
- Carve-out (verified against `style-catalog.md`): styles
  `semi-realistic-digital-painting`, `painterly-realism-cinematic`,
  `concept-art-cityscape` ("photo-real lighting"), `photobash-epic-poster`
  ("realistic textures") are painterly art, NOT live-action — detection must not
  false-positive on the words "semi-realistic" / "photo-real lighting" /
  "realistic textures".

### Whole-Plan Consistency Sweep — Session 1
- Category count reconciled 7→8 across overview/acceptance/out-of-scope.
- phase-03 references count corrected 9→10 (plan.md acceptance had no count line).
- No stale terms / contradictions remain. Recommendation: **proceed**.

### Implementation note — Session 2 (2026-06-22)
- BUG found during integration smoke (not anticipated in planning): GORE/SEXUAL/
  PHOTOREAL_VIDEO regexes matched the SAME words used in the Layer-4 safety
  negatives ("no nudity", "no graphic gore or blood splatter", inline "no
  live-action …"), which appear in EVERY assembled output — so `--fix` mangled the
  gate's own safety line. Fixed with a negation-context guard in
  `check_content_safety.py`: those 3 categories skip a hit preceded by
  no/not/avoid(ing)/without/never/ban(ned) within ~30 chars. Brand/IP/likeness/
  religion are NOT guarded. Verified: positive violations still stripped, safety
  negatives preserved, re-scan exits 0.
- Acceptance #7 (full Agy end-to-end on a real chapter) NOT executed here: requires
  the headless Agy model loop and RULE 0 bans external-model calls in this env.
  Substituted a deterministic integration smoke with assembled-style image+video
  fixtures using the exact STEP 7/8 invocation; all gates pass.
