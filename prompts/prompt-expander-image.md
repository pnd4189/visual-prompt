# Image Prompt Expander — Per Scene

## ROLE
Expand one scene row from the scene-plan into a full image prompt block,
matching the format spec in `@references/visual-prompt-template.md` exactly.

## INPUT (per scene)
- `scene_row` — `{scene_id, chapter, scene_tag, characters, synopsis, ...}`
- `bible` — `character-bible.md` content (filter to characters in this scene)
- `genre` — detected genre keyword
- `chapter_excerpt` — the relevant chapter text ONLY (NOT full chapters.json)
- `active_style` — `.work/active-style.md` content (one chosen style entry)
- `cache_key` — SHA1(input.hash + bible.hash + plan.hash + style.hash + scene_row_text)

## CRITICAL — CHAPTER EXCERPT RULE
Load ONLY the chapter referenced by `scene_row.chapter`. Do NOT load
`chapters.json` whole — for 18k-word files, that blows the context.

## TASK
1. Load `@references/visual-prompt-template.md` (image format section) AND
   `.work/active-style.md` (the chosen style entry). The `Style block` field of
   active-style is the Style section base; its `reference anchors` replace any
   fixed cinema reference.
2. Load `@references/scene-tag-camera-mapping.md` — pick row matching
   `scene_row.scene_tag` for Camera defaults.
3. Load `@references/negative-lists.md` — compose 4-layer negative (universal
   anti-Western + genre + AI-defense + style negatives), cap 24 items. Layer 4 =
   first 4 items from the `style negatives` field of `.work/active-style.md`.
4. Load `@references/genre-keywords.md` — translate VN trigger words from
   the chapter excerpt into EN visual vocabulary.
5. Build the prompt with these EXACT sections in order:
   ```
   Camera: ...
   Setting: ...
   Subject: <IDENTITY ANCHOR VERBATIM from bible> + scene state
   Style: <Style block from active-style + cite its reference anchors>
   Lighting: ...
   Negative: ...
   ```
6. Target 200–300 words total. Hard penalty if >320.
7. The `Style` section MUST use the `Style block` of `.work/active-style.md` and
   cite at least one of its `reference anchors`. Do NOT inject a fixed cinema
   reference — the chosen style decides the look.

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
3. **Negative count check** — 24 items max (10+5+5+4), comma-separated. The last
   4 are the style negatives from `.work/active-style.md`.
4. **Style reference check** — the `reference anchors` of the chosen style (from
   `.work/active-style.md`) appears in the Style section. If not → add it. There
   must be NO fixed cinema reference unless it IS the chosen style's anchor.
5. **All 6 sections present** with exact headers `Camera:`, `Setting:`,
   `Subject:`, `Style:`, `Lighting:`, `Negative:`.

## STDOUT SUMMARY
```
Scene <NNN> image written: <wc> words, anchor verified for <N> chars
```
