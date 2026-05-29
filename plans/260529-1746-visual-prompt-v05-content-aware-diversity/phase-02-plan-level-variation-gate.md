---
phase: 2
title: "Plan-Level Variation Gate"
status: completed
priority: P1
effort: "2-3h"
dependencies: [1]
---

# Phase 2: Plan-Level Variation Gate

## Overview

Deterministic backstop after Pass 1: reject a scene plan with adjacent-duplicate
scenes (same tag + same characters + same location) or invalid/fragment
synopses, so monotony cannot pass silently into the expander.

## Requirements

- Functional: a script parses `.work/scene-plan.md` and emits a violations list.
- Functional: flag any pair within a sliding window (default 10 indices) sharing
  the same scene_tag AND >70% character overlap AND same location cue.
- Functional: flag synopsis that is empty, too short, starts mid-word, or is a
  raw text slice (heuristic: no sentence-like structure).
- Functional: orchestrator regenerates the plan (or revises flagged rows) when
  violations exist, capped at max retries.
- Non-functional: pure-Python, no new deps; exit code signals pass/fail.

## Architecture

- **New file `scripts/validate_scene_plan.py`:**
  - Parse the markdown table (reuse the row regex shape already used by the
    grep in brainstorm; robust to leading/trailing pipes).
  - Location cue: derive from synopsis keywords (no separate column exists) —
    cheap noun/location heuristic; if unreliable, fall back to tag+character
    duplicate detection only (documented).
  - Output JSON: `{ total, violations: [{type, scene_ids, reason}], ok }` to stdout;
    exit 0 if `ok`, exit 2 if violations (1 reserved for IO errors).
- **Orchestration (toml STEP 5.5, new):** run validator after scene-plan write.
  If violations → instruct planner to revise ONLY flagged scene_ids (re-emit
  those rows), rewrite plan, re-validate. Cap at 2 retries; on final failure,
  WARN and proceed (do not hard-block a run).

## Related Code Files

- Create: `scripts/validate_scene_plan.py`
- Modify: `commands/visual-prompt.toml` (add STEP 5.5 validation + bounded revise loop)
- Modify: `prompts/scene-planner.md` (revise-flagged-rows contract for the retry path)

## Implementation Steps

1. Write `validate_scene_plan.py`: table parser + adjacent-duplicate check
   (window=10, char-overlap>70%, same tag) + synopsis-validity check.
2. Define synopsis-validity heuristic conservatively to avoid false positives
   (min word count, must not start lowercase-mid-word, must contain a verb-like
   token or punctuation — keep simple).
3. Smoke-test on a synthetic plan with planted duplicates + fragment synopsis
   (expect violations) and on a clean plan (expect ok).
4. Add toml STEP 5.5: call validator, parse JSON, run bounded revise loop.
5. Add the "revise only flagged scene_ids" contract to `scene-planner.md`.

## Success Criteria

- [ ] Validator flags planted adjacent-duplicate triples and fragment synopses.
- [ ] Clean plan returns `ok: true`, exit 0.
- [ ] toml runs the gate after Pass 1 with a capped retry loop.
- [ ] Final-failure path warns and proceeds (no infinite loop, no hard crash).

## Risk Assessment

- Risk: location heuristic from synopsis is noisy → false duplicates.
  Mitigation: make location optional in the triple; tag+character duplicate is the firm signal, location is a tie-breaker.
- Risk: over-strict synopsis check rejects valid short lines.
  Mitigation: conservative thresholds; tune against the real sample plan.
