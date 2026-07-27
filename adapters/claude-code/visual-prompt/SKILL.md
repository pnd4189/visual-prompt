---
name: visual-prompt
description: Generate grounded, non-repetitive image prompts from a Vietnamese novel. Use only when the user explicitly invokes /visual-prompt; add video or music only when explicitly requested.
disable-model-invocation: true
argument-hint: "<input-path> [flags] [tạo video prompt] [tạo music prompt]"
---

# Visual Prompt for Claude Code

Act as the active parent model and perform all creative generation yourself.
Do not invoke subagents, Agent Teams, delegation, parallel writers, external
LLMs, model APIs, or runtime prompt-generating scripts.

## Resolve the canonical skill files

Resolve the real directory containing this `SKILL.md` as `SKILL_DIR`.

- For the repository symlink install, the canonical root is `SKILL_DIR/../../../`.
- For a copied install, use the nearest directory containing
  `commands/visual-prompt.toml`, `prompts/`, `references/`, and `scripts/`.

Before writing anything, read completely:

1. `<root>/references/strict-generation-contract.md`
2. `<root>/commands/visual-prompt.toml`
3. The prompt contracts named by the command for the current step

Follow the command file exactly. It is the shared workflow authority; do not
create a shortened private workflow or alter its gates.

## Invocation and media defaults

`$ARGUMENTS` is the full text after `/visual-prompt`.

- Default: QA output + image prompts only.
- `--video`, `--videos N`, or a clear request such as “tạo video prompt” enables
  video.
- `--music`, `--music N`, or a clear request such as “tạo music/nhạc prompt”
  enables music.
- `--no-video` and `--no-music` always win.

Do not infer optional media from the story's mention of YouTube, audio, or music.

## Generation discipline

Generate scenes in parent-only micro-batches of at most three consecutive rows.
Write each scene separately and verify source anchors, artifacts, and gates before
continuing. If a gate still fails after its bounded retry, stop with exact scene
IDs and reasons. Never weaken validators, hand-edit final assembled output, or
fabricate a scene to satisfy a count.
