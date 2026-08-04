---
title: Agy/Antigravity subagent and parallel-worker capability review
date: 2026-07-29
status: complete
---

# Agy/Antigravity Subagent Review

## Summary

Local evidence says `visual-prompt` is intentionally single-model, fail-closed, and anti-orchestration.
The repo contract forbids subagents, teams, delegation, parallel workers, and runtime prompt generators.

At the CLI layer, `agy` exposes an `agent` subcommand, but only for listing agents.
`antigravity` is a VS Code-style shell with chat/server/tunnel entrypoints, not a public orchestration API.
Runtime logs do show Antigravity internals using `subagent_manager.go`, so internal subagents exist in the product.
That does **not** make them safe or available to `visual-prompt`, because the skill contract explicitly forbids them.

## Findings

### 1. Repo contract blocks parallel orchestration

- `README.md:30-33` says the active parent model writes each scene, with no subagent, no parallel generation, no batch scripts.
- `commands/visual-prompt.toml:15-39` repeats the hard ban on subagents, agent teams, delegation, parallel workers, and external model calls.
- `adapters/codex/visual-prompt/SKILL.md:8-10` also says never use subagents, teams, delegation, parallel writers, external LLMs, or runtime prompt generators.

Credibility: highest. This is the canonical local contract.

### 2. `agy` CLI has no visible subagent orchestration surface

Verified by `agy --help` and `agy agent --help`:

- `agy --help` exposes `agent`, `agents`, `plugin`, `plugins`, `models`, `install`, `update`.
- `agy agent --help` only says “List available agents”.

There is no public `spawn`, `parallel`, `worker`, or delegation command in the CLI help.

Credibility: high. This is the actual installed binary help.

### 3. `antigravity` CLI is a GUI shell, not a task fan-out runner

Verified by `antigravity --help`:

- It exposes editor/window flags, extension management, MCP registration, and subcommands `chat`, `serve-web`, and `tunnel`.
- No public worker pool, subagent launcher, or parallel execution command is advertised.

Credibility: high. This is the installed binary help.

### 4. Antigravity runtime internally manages subagents

`~/.gemini/antigravity-cli/log/cli-20260725_174131.log:37-40` shows CLI backend startup with `cascadeManager=true codeAssist=true`.
`~/.gemini/antigravity-cli/log/cli-20260726_141309.log:731-779` shows `subagent_manager.go` auto-approving subagent steps and tool confirmations.

This is real evidence that the product runtime has subagent machinery.
It is **not** evidence that `visual-prompt` should use it, because the skill contract blocks it.

Credibility: high for existence, low for suitability.

## Trade-off Matrix

| Option | Quality | Safety | Consistency | Throughput | Fit for `visual-prompt` |
|---|---:|---:|---:|---:|---:|
| Single active model, sequential micro-batches | High | High | High | Low | Best |
| Runner-level parallel Agy processes on disjoint files | Medium | Medium | Medium | High | Only for read-only, non-creative prep |
| In-skill subagents / delegation | Unclear | Low | Low | High | Reject |

## Recommendation

1. Keep the current design: one active model, sequential micro-batches of at most 3 scenes, fail-closed validators.
2. Do **not** use in-skill subagents or delegation. The repo contract already forbids them.
3. If throughput becomes a hard requirement later, only consider runner-level parallel Agy processes for isolated, read-only prep work on distinct inputs. Never fan out creative scene generation across processes without a single merge gate.

Why this ranking:

- Creative quality in this project depends on shared context, continuity, and strict grounding.
- Parallel writers risk drift in character bible, scene anchor continuity, and repeated setting/camera/action patterns.
- The repo already treats quota failures as a stop condition, not as a reason to split work across generators.

## Adoption Risk

- Internal Antigravity subagents are a moving target and not part of the skill contract.
- Runner-level parallel processes are operationally possible but fragile: shared `.work/` state, cache races, and merge conflicts can corrupt continuity.
- The lowest-risk path is the existing single-process flow.

## Limitations

- I did not browse upstream web docs; this is a local-state review only.
- I did not run a live orchestration experiment, because the skill contract explicitly forbids it and the task was research-only.
- I did not inspect private Antigravity source code; conclusions about internal subagents come from logs, not source.

## Sources

- [README.md](/home/dung/VIBE_CODING/1.%20OTHERS/visual-prompt/README.md)
- [commands/visual-prompt.toml](/home/dung/VIBE_CODING/1.%20OTHERS/visual-prompt/commands/visual-prompt.toml)
- [adapters/codex/visual-prompt/SKILL.md](/home/dung/VIBE_CODING/1.%20OTHERS/visual-prompt/adapters/codex/visual-prompt/SKILL.md)
- `agy --help`
- `agy agent --help`
- `antigravity --help`
- `~/.gemini/antigravity-cli/log/cli-20260725_174131.log`
- `~/.gemini/antigravity-cli/log/cli-20260726_141309.log`
