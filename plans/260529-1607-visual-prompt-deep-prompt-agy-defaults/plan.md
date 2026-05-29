---
title: Visual Prompt v0.4 — Deep Prompt Quality + Agy Defaults
description: >-
  Make /visual-prompt default to 120-150 image prompts and at least 20 video
  prompts, enforce high-detail prompt structure, improve
  action/map/multi-character scene diversity, and remove unsafe style/likeness
  copying language for Agy CLI.
status: completed
priority: P1
branch: main
tags:
  - skill
  - antigravity
  - agy-cli
  - prompts
  - copyright-safety
  - xianxia
blockedBy: []
blocks: []
created: '2026-05-29T09:07:39.715Z'
createdBy: 'ck:plan'
source: skill
---

# Visual Prompt v0.4 — Deep Prompt Quality + Agy Defaults

## Overview

Upgrade `/visual-prompt` for Antigravity/Agy CLI production use. Default output
stays four files, but scene count increases to ~120-150 image prompts and at
least 20 video prompts. Prompt generation must follow the deep structure seen in
the Bình Thiên Sách master template: story DNA, identity/prop locks, layered
backgrounds, camera, lighting, palette, action, audio, negatives, and self-checks.

The plan also removes prompt language that asks models to copy named IP/artist/
celebrity likenesses. Style steering becomes descriptive and original; no copied
web images or famous faces.

## Context Links

- Template reference: `/home/dung/cloud/gdrive/YOUTUBE AUDIO/BÌNH THIÊN SÁCH/BINH THIEN SACH - VO TOI/template/binh-thien-sach-master-prompt-final.md`
- Code scout: [`reports/scout-report.md`](./reports/scout-report.md)
- Research 1: [`research/researcher-prompt-depth-and-counts.md`](./research/researcher-prompt-depth-and-counts.md)
- Research 2: [`research/researcher-copyright-safety-and-agy.md`](./research/researcher-copyright-safety-and-agy.md)
- Red team: [`reports/red-team-report.md`](./reports/red-team-report.md)

## Scope

In scope: default count policy; deep prompt format; scene diversity; copyright/
likeness prompt-safety; Agy CLI wording; docs cleanup.

Out of scope: new output files, reference-image workflow, new dependencies, new
public flags, QA/TTS/bible architecture changes, adaptive music count changes.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Default Counts and Agy Command Contract](./phase-01-default-counts-and-agy-command-contract.md) | Completed |
| 2 | [Copyright-Safe Deep Prompt Template](./phase-02-copyright-safe-deep-prompt-template.md) | Completed |
| 3 | [Scene Diversity and Action Planning](./phase-03-scene-diversity-and-action-planning.md) | Completed |
| 4 | [Expander Quality Gates and Music Detail](./phase-04-expander-quality-gates-and-music-detail.md) | Completed |
| 5 | [Validation and Documentation](./phase-05-validation-and-documentation.md) | Completed |

## Dependencies

- Builds on v0.1/v0.2/v0.3 plans; all are `implemented`.
- No cross-plan blocker.
- Implementation should stay surgical: edit existing command, prompt, reference,
  docs, and count-script files only.

## Key Decisions

| Topic | Decision |
|---|---|
| Default images | Auto path targets `120-150`; explicit `--images N` still wins. |
| Default videos | Auto path uses minimum `20`; explicit `--videos M` still wins. |
| Outputs | Keep `_qa.txt`, `_image_prompts.txt`, `_video_prompts.txt`, `_music_prompts.txt`. |
| Safety | Ban copying web images, famous faces, celebrity likeness, named-character likeness, and living-artist style requests. |
| Style | Replace named IP/artist anchors in generated prompt language with descriptive original style vocabulary. |
| Scene mix | Require action/combat/ritual/reveal, map-scale environment, and multi-character scenes; avoid main-character-only monotony. |
| Agy | Treat Antigravity/Agy CLI as the target; remove Gemini CLI as a supported runtime from docs/command prose. |

## Validation Gates

- Unit/smoke test `scripts/calc_scene_count.py` for auto and override count cases.
- Static grep must find no unsafe generated-prompt instructions such as `in the style of WLOP`, celebrity likeness, or copying images.
- Prompt fixture check verifies at least 120 image blocks and at least 20 video blocks on a synthetic input or dry-run artifact.
- Manual review of prompt files must confirm deep-detail self-checks are explicit and non-optional.
