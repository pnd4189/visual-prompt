---
description: Generate grounded image prompts from a Vietnamese novel (QA, video, and music are opt-in)
argument-hint: <input.txt> [--qa] [--video] [--music]
---

Invoke the native `$visual-prompt` skill with the complete user argument string
below. Preserve default image-only + skip-QA behavior unless the user explicitly
requests `--qa`, video, or music; `--no-qa`, `--no-video`, and `--no-music`
always win.

User arguments:
$ARGUMENTS
