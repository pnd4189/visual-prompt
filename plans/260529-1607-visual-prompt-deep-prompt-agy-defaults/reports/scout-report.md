# Scout Report

## Summary

- Project is a text-based Agy/Antigravity skill plugin: `commands/visual-prompt.toml`, `SKILL.md`, `prompts/`, `references/`, `scripts/`.
- No package manifest; Python scripts do I/O only.
- Existing plans v0.1, v0.2, v0.3 are all `implemented`; no active blocker.

## Relevant Files

| File | Finding |
|---|---|
| `scripts/calc_scene_count.py` | Auto count is `images = round(wordcount / 200)`, `videos = round(images / 7)`, min 5/2. |
| `commands/visual-prompt.toml` | Top says "active Gemini Ultra agent"; workflow still uses `.gemini` bible paths. |
| `prompts/scene-planner.md` | Planner optimizes coverage and uniqueness, not high-count action/map diversity. |
| `prompts/prompt-expander-image.md` | Image target is 200-300 words and six sections. |
| `prompts/prompt-expander-video.md` | Video uses 5-part formula and 400-800 words. |
| `prompts/music-prompt-builder.md` | Music count behavior already matches user requirement; detail can be improved. |
| `references/style-catalog.md` | Stable 18 ids, but many paste-ready blocks cite named IP/artist/style anchors. |
| `references/visual-prompt-template.md` | Canonical template is useful but too shallow for requested master-template-level detail. |
| `HUONG-DAN-SU-DUNG.md` | Still says Antigravity CLI or Gemini CLI and ~45 images + 6 videos. |

## Constraints

- Keep four output files.
- Keep existing flags; overrides must remain exact.
- Do not add dependencies.
- Do not create replacement `_v2` files.
- Avoid modifying generated sample outputs unless explicitly requested.

## Open Questions

- Whether Agy still uses `.gemini` filesystem paths for extensions/bibles should be verified during implementation if install behavior is touched.
