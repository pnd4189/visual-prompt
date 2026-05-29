# Researcher Report: Copyright Safety and Agy Target

## Summary

The active repo contains several style prompts that steer generation with named
films, games, anime, studios, and artists. The user's requirement is not only
"do not copy images"; it specifically includes avoiding famous faces and keeping
outputs original. The plan should remove positive imitation directives from active
prompt files.

## Findings

- `references/style-catalog.md` has stable ids; keep them.
- Paste-ready style blocks frequently use "in the style of" named IP/artists.
- Prompt instructions currently ask expanders to cite `reference anchors`; this
encourages generated prompts to include those names.
- Docs still mention Gemini CLI as an equivalent runtime, while user wants Agy CLI.
- Music prompt references also include named score/style registers; these should
be rewritten descriptively where paste-ready.

## Safety Contract

Active generated prompts should not ask for:
- copied web image composition
- celebrity/famous actor face
- known fictional character likeness
- living artist style mimicry
- exact branded/IP look
- watermark/logo/text unless explicitly part of a safe UI/thumbnail workflow

Allowed:
- generic cultural and medium descriptors
- historical art traditions in broad terms
- public-domain motifs and original fantasy details
- internal character bible identity anchors

## Agy Contract

Use language such as:
- "active Antigravity/Agy model"
- "Agy CLI skill command"
- "Antigravity workflow"

Avoid saying Gemini CLI is supported runtime. Paste targets like Veo3, Seedance,
Lyria, ChatGPT, Qwen can remain as downstream tools if still useful.

## Recommendations

- Replace `reference anchors` requirement with `style descriptors`.
- Keep old plan reports unchanged; only active prompt/reference/docs matter.
- Add static grep to validation so future edits do not reintroduce unsafe wording.
