# Visual Prompt v0.10.0 — Fail-Closed Quality Gates

**Date**: 2026-07-20  
**Severity**: High  
**Component**: visual-prompt skill — parsers, artifact validators, batch resume, history  
**Status**: Implemented and locally verified

## What Happened

The anti-repetition upgrade exposed contract drift between generated prompt formats,
validators, and batch-resume behavior. Several gates could accept empty, malformed,
stale, or mismatched artifacts. v0.10.0 aligns those contracts and makes completion
fail closed before outputs enter history or become resumable.

## Key Changes

- Added one canonical similarity parser for image, video, and music prompts. It
  rejects zero blocks, duplicate IDs, orphan music tags, empty comparable fields,
  and malformed canonical output.
- Bound scene artifacts and assembled outputs to the scene plan's declared image
  and video totals, exact IDs, order, and video subset. Suffixed scene IDs are
  normalized without collapsing distinct scenes.
- Made music plans self-verifying: exact region schema, contiguous coverage,
  declared count, genre, QA/plan/style hashes, cache keys, allowed moods, and
  numbered files are checked together. Music indices now support 1000+.
- Persisted the selected genre in `.work/genre.txt`, so restored music caches
  cannot silently reuse a plan from another genre.
- Replaced PID-file history locking with an OS advisory lock and atomic writes,
  preventing stale locks and concurrent lost updates.
- Added a verified completion manifest containing configuration and artifact
  hashes. Batch resume skips only verified, unchanged outputs; malformed or edited
  files are regenerated.
- Sanitized series-derived paths and tightened final content-safety and similarity
  gate ordering before history/cache publication.

## Decisions

- Existing similarity thresholds remain unchanged; the fix strengthens evidence
  and lifecycle guarantees rather than changing accepted creative policy.
- Validators share explicit file contracts and reject ambiguity instead of
  inferring success from counts or marker substrings.
- Resume state is an integrity record, not merely an existence check.

## Verification

- Contract regression suite: **24/24 passed**.
- Concurrent history stress: **30/30 passed**.
- Python compile, shell syntax, TOML/JSON parsing, targeted artifact probes, and
  size-budget checks passed.
- Final adversarial code audit: **PASS**, with no release-blocking findings.

## Impact

Generated bundles now enter cache/history only after their declared plan, content,
IDs, hashes, and safety checks agree. Interrupted runs remain resumable, while
stale or manually modified outputs can no longer bypass validation.

## Open / Not Verified

- The original raw chapter-16 baseline fixture was unavailable, so that exact
  historical comparison was not reproduced.
- A real end-to-end Agy regeneration/resume run remains pending.
- No commit was created during this session.
