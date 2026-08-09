---
phase: 2
title: "Scene Provenance Gates"
status: completed
effort: "medium"
---

# Phase 2: Scene Provenance Gates

## Overview

Accept only scene artifacts that can be traced back to a primary-session direct
write and reject filler padding that tries to fake prompt depth.

## Implementation Steps

1. Extend `scripts/check_run_legit.py` with `--require-authorship` and
   `--authorship-log`.
2. Require matching `basename + SHA-256 + primary conversation` provenance for
   scene files.
3. Flag `Padding:` blocks and numbered filler floods as hard legitimacy
   failures.
4. Keep canonical helper allowlists versioned with the skill release.

## Success Criteria

- [x] Missing or mismatched provenance fails the worker/full legitimacy gate.
- [x] Repetitive numbered filler cannot pass as “deep” prompt content.
- [x] Canonical guard scripts are recognized as legitimate skill helpers.
