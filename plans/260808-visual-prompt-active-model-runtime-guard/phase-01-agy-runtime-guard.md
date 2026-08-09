---
phase: 1
title: "Agy Runtime Guard"
status: completed
effort: "medium"
---

# Phase 1: Agy Runtime Guard

## Overview

Install a runtime hook path that Agy 1.1.11 actually discovers, then block
delegation, runtime generators, and non-primary artifact mutation at tool time.

## Implementation Steps

1. Keep plugin-local `hooks.json` for native validation.
2. Add workspace `.agents/hooks.json` so runner workspaces load the guard even
   when plugin-root hook discovery is skipped by Agy.
3. Add a setup-time merge into `~/.gemini/config/hooks.json` so direct
   `/visual-prompt` invocations from arbitrary folders still enforce the guard.
4. Route hook commands to `scripts/active_model_guard.py` and
   `scripts/active_model_policy.py`.

## Success Criteria

- [ ] ~~Agy runner workspaces load the guard from `.agents/hooks.json`.~~
  **Disproven 2026-08-09** on Agy 1.1.11: a probe hook placed there never fired in
  print or interactive mode. The workspace copy is inert, kept only for forward
  compatibility. Enforcement comes from two paths that do load — the global
  `~/.gemini/config/hooks.json` and the imported plugin's own `hooks.json` — which
  is why every hook event fires twice and the guard must stay idempotent.
- [x] Direct setup installs a global fallback hook without overwriting unrelated
  user hooks.
- [x] Delegation and runtime prompt generators fail closed.
- [x] The guard arms from the user's `/visual-prompt` turn, not from a marker the
  model must choose to read (fixed 2026-08-09; Agy stores only the raw user turn
  in `transcript_full.jsonl`).
