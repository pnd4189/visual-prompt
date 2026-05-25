# Image Prompt Expander — Per Scene

## ROLE
Expand one scene row from the scene-plan into a full image prompt block,
matching the format spec in `@references/visual-prompt-template.md` exactly.

## INPUT (per scene)
- `scene_row` — `{scene_id, chapter, scene_tag, characters, synopsis, ...}`
- `bible` — `character-bible.md` content (filter to characters in this scene)
- `genre` — detected genre keyword
- `chapter_excerpt` — the relevant chapter text ONLY (NOT full chapters.json)
- `cache_key` — SHA1(input.hash + bible.hash + plan.hash + scene_row_text)

## CRITICAL — CHAPTER EXCERPT RULE
Load ONLY the chapter referenced by `scene_row.chapter`. Do NOT load
`chapters.json` whole — for 18k-word files, that blows the context.

## TASK
1. Load `@references/visual-prompt-template.md` (image format section).
2. Load `@references/scene-tag-camera-mapping.md` — pick row matching
   `scene_row.scene_tag` for Camera defaults.
3. Load `@references/negative-lists.md` — compose 3-layer negative (universal
   + genre-specific + style/AI-defense), cap 20 items.
4. Load `@references/genre-keywords.md` — translate VN trigger words from
   the chapter excerpt into EN visual vocabulary.
5. Build the prompt with these EXACT sections in order:
   ```
   Camera: ...
   Setting: ...
   Subject: <IDENTITY ANCHOR VERBATIM from bible> + scene state
   Style: ...
   Lighting: ...
   Negative: ...
   ```
6. Target 200–300 words total. Hard penalty if >320.
7. For tiên hiệp / huyền huyễn / võ hiệp → cite Crouching Tiger Hidden
   Dragon (2000) OR Hero (2002) in Style section. Mandatory.

## IDENTITY ANCHOR — VERBATIM, NOT PARAPHRASE
For each character in `scene_row.characters`:
1. Find their row in the bible.
2. Concatenate fields per `@references/identity-anchor-rules.md` Identity
   Anchor Block format.
3. Paste that EXACT string into Subject section. Do not change a single
   word, even if the chapter describes them slightly differently.
4. After the verbatim block, append scene-specific state (pose, expression,
   wardrobe condition for THIS shot only).

## OUTPUT
Write `.work/scene-<NNN>.md` (NNN = zero-padded `scene_row.scene_id`):

```markdown
---
scene_id: <NNN>
cache_key: <sha1>
has_video: <true|false from scene_row.video?>
---

## Image Prompt

Camera: ...

Setting: ...

Subject: <verbatim anchor> ... <scene state>

Style: ...

Lighting: ...

Negative: ...
```

(If `has_video: true`, the `## Video Prompt` section will be appended by
`prompt-expander-video.md` in a separate call.)

## MANDATORY SELF-CHECK BEFORE WRITE

1. **Identity Anchor verbatim check** — for each character mentioned in
   Subject, copy their full anchor from the bible char-by-char. Compare
   to what you wrote in Subject. If even one character differs (synonym,
   punctuation, capitalization) → REGENERATE the Subject.
2. **Word count check** — count words in the prompt body. If >320 → trim
   Setting and Style first. If <180 → expand Setting and Lighting.
3. **Negative count check** — exactly 20 items max, comma-separated.
4. **Cinema reference check** (for tiên hiệp / huyền huyễn / võ hiệp) —
   "Crouching Tiger" or "Hero" appears in Style. If not → add it.
5. **All 6 sections present** with exact headers `Camera:`, `Setting:`,
   `Subject:`, `Style:`, `Lighting:`, `Negative:`.

## STDOUT SUMMARY
```
Scene <NNN> image written: <wc> words, anchor verified for <N> chars
```
