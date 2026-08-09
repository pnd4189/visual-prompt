---
title: "Visual Prompt Active Model Runtime Guard"
description: "Fail-closed runtime guard so Agy primary sessions must author every scene prompt directly, with hook-backed provenance and worker-safe speed."
status: completed
priority: P1
branch: "main"
tags: []
blockedBy: []
blocks: []
created: "2026-08-08T09:12:30.711Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt Active Model Runtime Guard

## Overview

Definitive fix for the recurring Agy/Gemini bypass where the active model falls
back to repetitive script-generated prompts. The runtime now enforces
primary-session authorship, denies delegation/runtime generators, and requires
matching SHA-256 provenance for every accepted scene artifact.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Agy Runtime Guard](./phase-01-agy-runtime-guard.md) | Completed |
| 2 | [Scene Provenance Gates](./phase-02-scene-provenance-gates.md) | Completed |
| 3 | [Worker Provenance Preservation](./phase-03-worker-provenance-preservation.md) | Completed |
| 4 | [Regression Verification](./phase-04-regression-verification.md) | Completed |

## Dependencies

- Plugin/global hooks use plugin-root commands; workspace `.agents/hooks.json`
  uses `../scripts/` because Agy executes it from the customization directory.
- `scripts/run-folder.sh` must keep the worker fast path while honoring the
  runtime guard.
- `scripts/check_run_legit.py` is the final fail-closed gate for authorship and
  padding/template regressions.
