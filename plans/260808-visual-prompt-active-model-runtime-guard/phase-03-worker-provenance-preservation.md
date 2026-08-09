---
phase: 3
title: "Worker Provenance Preservation"
status: completed
effort: "medium"
---

# Phase 3: Worker Provenance Preservation

## Overview

Keep `VP_WORKERS` fast by letting multiple isolated primary sessions expand
different scene ranges, while preserving per-worker authorship logs through join.

## Implementation Steps

1. Run worker sessions with `--agent visual-prompt-writer` and `--sandbox`.
2. Stage `.agents`, `scripts`, `prompts`, and `references` into every worker
   workspace so the runtime hook loads from the local workspace root.
3. Emit per-worker authorship logs, validate them during join, then merge them
   into the coordinator log before the tail session.
4. Keep worker ownership strict: only assigned `scene-NNN.md` files are writable.

## Success Criteria

- [x] Worker fast path keeps running in parallel.
- [x] Worker legitimacy checks require authorship provenance.
- [x] Coordinator tail sees merged worker provenance before final gates.
