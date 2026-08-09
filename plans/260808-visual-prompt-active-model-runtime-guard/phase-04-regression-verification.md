---
phase: 4
title: "Regression Verification"
status: completed
effort: "medium"
---

# Phase 4: Regression Verification

## Overview

Verify unit gates, hook discovery, and live Agy smoke behavior after the runtime
guard rollout.

## Implementation Steps

1. Run Python unit tests for the guard and prompt contract gates.
2. Validate plugin metadata with `agy plugin validate .`.
3. Smoke-test hook discovery and a forbidden runtime generator attempt through
   Agy itself.
4. Review the final diff and keep only the smallest enforceable fix.

## Success Criteria

- [x] Guard unit tests pass.
- [x] Plugin validation passes.
- [x] Live Agy smoke shows the forbidden generator is blocked by the hook.
- [x] Post-change review finds no bypass regression in the fast path.
