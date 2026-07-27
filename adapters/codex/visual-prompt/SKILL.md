---
name: visual-prompt
description: Generate grounded, non-repetitive image prompts from a Vietnamese novel. Use when the user asks for /visual-prompt, scene image prompts, or explicitly asks to add video or music prompts.
---

# Visual Prompt for Codex CLI

You are the active parent model. You must create every creative artifact yourself.
Never use subagents, teams, delegation, parallel writers, external LLMs, model APIs,
or runtime prompt generators.

## Resolve the canonical skill files

Resolve the real directory containing this `SKILL.md` as `SKILL_DIR`.

- For the repository symlink install, the canonical root is `SKILL_DIR/../../../`.
- For a copied install, the canonical root is the nearest directory containing
  `commands/visual-prompt.toml`, `prompts/`, `references/`, and `scripts/`.

Read these files completely before acting:

1. `<root>/references/strict-generation-contract.md`
2. `<root>/commands/visual-prompt.toml`
3. The prompt contracts named by the command for the current step

The command file is the single workflow authority. Do not summarize it into a
shorter private brief and do not invent a replacement workflow.

## Invocation and media defaults

The user arguments are supplied after `/prompts:visual-prompt` (custom prompt
shim) or after `$visual-prompt` (native Codex skill invocation).

- Default: QA output + image prompts only.
- `--video`, `--videos N`, or a clear request such as “tạo video prompt” enables
  video.
- `--music`, `--music N`, or a clear request such as “tạo music/nhạc prompt”
  enables music.
- `--no-video` and `--no-music` always win.

Bind the complete argument string to `{{args}}` in the command contract, then
execute every step in order. Do not infer optional media from the story's mention
of YouTube or audio.

## Generation discipline

Generate scene files in parent-only micro-batches of at most three consecutive
rows. Write each scene separately, verify its source anchor and artifact structure,
then continue. If a gate or helper fails after its bounded retry, stop and report
the exact scene IDs; never weaken a validator or fabricate a replacement.
