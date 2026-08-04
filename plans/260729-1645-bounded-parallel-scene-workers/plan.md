---
title: "Visual Prompt Opt-In Bounded Parallel Scene Workers"
description: "Opt-in runner-level 3-worker mode for Pass-2 scene expansion with isolated ownership, fail-closed gates, and default single-mode compatibility."
status: in-progress
priority: P1
effort: 12h
branch: "main"
tags: [visual-prompt, runner, parallel-workers, tdd, fail-closed]
blockedBy:
  - "plans/260714-1044-vp-anti-repetition-optimal-upgrade/plan.md"
blocks: []
created: "2026-07-29"
source: skill
---

# Visual Prompt Opt-In Bounded Parallel Scene Workers

## Overview
Opt-in runner-level parallelism for Pass-2 only. Default stays single-worker; enabled mode launches 3 isolated `agy` sessions (spawned via the parameterized pexpect harness — see Decisions) on disjoint scene-ID ranges, while the coordinator keeps QA, bible/style/hash freezes, similarity/history publish, completion marker, and final gates. This requires an explicit `/visual-prompt` worker submode because Agy exposes no native worker/subagent API and the current command always runs the full pipeline [README.md:30-33][commands/visual-prompt.toml:438-447][adapters/codex/visual-prompt/SKILL.md:47-50][plans/reports/researcher-260729-agy-antigravity-subagents.md:61-83].

## Decisions (brainstorm 260804-1927, user-approved)

Source: `plans/reports/brainstorm-260804-1927-vp-teamwork-preview-rejected-bounded-parallel-report.md`

- Vehicle confirmed = this plan (runner-level bounded parallel). The alternative
  (auto-trigger agy `/teamwork-preview` subagent teams inside the run) was
  REJECTED: violates RULE 0 via the exact mechanism that caused past bypass
  incidents; built-in workers are blind to the skill contract; no write fences
  for `.work/`; unproven in headless `-p`; gates cannot detect subagent
  provenance. Do not relitigate without new evidence.
- Default worker count = 3 (`VP_WORKERS`, cap by remaining scene rows);
  serial path must stay byte-for-byte unchanged when the env is absent.
- RULE 0 stays intact for in-run models; delegation exists ONLY at runner
  level (bash-spawned `agy` sessions), recorded as the explicit exception.
- Speed ceiling is Gemini per-minute rate limit, not monthly quota; Phase 4
  benchmark decides whether 3 holds.
- Spawn vehicle = parameterized reuse of the pexpect harness in `run-folder.sh`,
  NOT `agy -p` (user decision 2026-08-04): the WIP committed in Phase 0 replaced
  the `agy -p` one-shot with that harness to fix the yield-turn/approval incident
  class; workers inherit it per-worker (token, workdir, markers, logs).

## Phases

| Phase | Name | Status |
|---|---|---|
| 0 | [Close v0.10 Plan (Prerequisite)](./phase-00-close-v010-plan.md) | Completed |
| 1 | [Lock Contracts and Regression Tests](./phase-01-lock-contracts-and-regression-tests.md) | Completed |
| 2 | [Implement Isolated Scene Worker Mode](./phase-02-implement-isolated-scene-worker-mode.md) | Pending |
| 3 | [Implement Coordinator Fan-out and Join](./phase-03-implement-coordinator-fan-out-and-join.md) | Pending |
| 4 | [Integration Validation and Rollout](./phase-04-integration-validation-and-rollout.md) | Pending |

## Dependencies
Phase 0 closes `plans/260714-1044-vp-anti-repetition-optimal-upgrade/plan.md`
(commit WIP, root quarantine, release discipline) — audit 260804-1910 found its
phases 2-6 already shipped but never formally closed; both plans share the same
gates, retry semantics, and runner contract, so the gate-verification surface
must settle first. Phase 1 freezes the current serial baseline before any
parallel worker code lands. Phase 2 must land before fan-out/join. Phase 4
needs explicit validation, benchmark, and restart before activation.
