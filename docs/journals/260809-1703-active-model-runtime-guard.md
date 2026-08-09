---
title: "Active Model Runtime Guard"
date: "2026-08-09 17:03"
severity: "High"
component: "Agy active-model runtime guard"
status: "Resolved"
---

# Active Model Runtime Guard

## Context

The active-model contract kept drifting in Agy because prompt wording was not enough. The real bug was that Agy 1.1.x could miss legacy plugin hooks, so the model still had a path to delegate, spawn runtime generators, or patch scene files without proving authorship. That made the whole “primary model writes every scene directly” rule a polite suggestion instead of an enforced boundary.

## What Happened

We hardened the pipeline across setup, runtime hooks, provenance checks, and batch execution. The guard now installs into `~/.gemini/config/hooks.json` without clobbering unrelated hooks, uses a stable launcher script so the repo path with spaces does not break hook execution, and rejects non-primary mutation at tool time. The legitimacy gate now requires matching SHA-256 provenance for scene files and fails closed on missing logs, stale hashes, template junk, and filler floods.

The plan’s regression-verification phase is marked completed, covering unit gates, `agy plugin validate .`, live Agy smoke checks, and final diff review.

## Reflection

The frustrating part is that this should have been obvious earlier: if the model can still write around the contract, then the contract is not real. We spent time reinforcing prose before accepting that the runtime had to be the source of truth. That is a bad shape for a system that claims to be fail-closed.

## Decisions

- Keep `VP_WORKERS` for speed, but treat each worker as its own guarded primary session.
- Merge the guard into the user’s existing hooks config instead of replacing it.
- Enforce authorship with SHA-256 provenance and reject patching of unproven scene files.
- Tighten content gates to catch numbered filler, generic template phrases, and boilerplate repetition.

## Next

The code path is now hardening-oriented instead of trust-oriented, but it still needs continued regression checking whenever Agy changes hook discovery behavior. Ownership for that stays with the runtime guard and batch driver path, and any future change should prove it cannot reintroduce a write path that bypasses provenance.
