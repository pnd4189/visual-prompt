# Image Prompt Expander — Per Scene

## ROLE
Expand one scene row from the scene-plan into a full image prompt block,
matching the format spec in `@references/visual-prompt-template.md` exactly.

## INPUT (per scene)
- `scene_row` — `{scene_id, chapter, scene_tag, characters, synopsis, ...}`
- `bible` — `character-bible.md` content (filter to characters in this scene)
- `genre` — detected genre keyword
- `mode` — `spectacle` (default) | `faithful` (controls amplification, see TASK 8)
- `chapter_excerpt` — the relevant chapter text ONLY (NOT full chapters.json)
- `active_style` — `.work/active-style.md` content (one chosen style entry)
- `cache_key` — SHA1(input.hash + bible.hash + plan.hash + style.hash + scene_row_text)

## CRITICAL — CHAPTER EXCERPT RULE
Load ONLY the chapter referenced by `scene_row.chapter`. Do NOT load
`chapters.json` whole — for 18k-word files, that blows the context.

## TASK
1. Load `@references/visual-prompt-template.md` (image format section) AND
   `.work/active-style.md` (the chosen style entry). The `Style block` field of
   active-style is the Style section base; use its descriptive style vocabulary.
   **Gold-standard bar (mandatory):** the `IMAGE EXAMPLE` in
   `@references/visual-prompt-template.md` is the depth + structure you must match
   — same 10 sections, same layered foreground/midground/background richness,
   same concreteness. Do NOT copy its content (adapt to THIS scene); DO match its
   depth. Reject your own output if it is shallower than that example.
2. Load `@references/scene-tag-camera-mapping.md` — pick row matching
   `scene_row.scene_tag` for Camera defaults.
3. Load `@references/negative-lists.md` — compose 5-layer negative (universal
   anti-Western + genre + AI-defense + likeness/copyright + style negatives), cap 28 items. Layer 5 =
   first 4 items from the `style negatives` field of `.work/active-style.md`.
4. Load `@references/genre-keywords.md` — translate VN trigger words from
   the chapter excerpt into EN visual vocabulary.
5. Build the prompt with these EXACT sections in order:
   ```
   Camera: ...
   Story DNA: ...
   Setting: ...
   Composition: ...
   Subject: <IDENTITY ANCHOR VERBATIM from bible> + scene state
   Action / Energy: ...
   Style: <Style block from active-style using original descriptors>
   Lighting / Color: ...
   Atmosphere: ...
   Negative: ...
   ```
6. Target 350–550 words total. Hard penalty if >650.
7. The `Style` section MUST use the `Style block` of `.work/active-style.md` and
   must NOT inject named IP, living artist, celebrity, or famous-character likeness
   references. The chosen style decides the look through original descriptors.
8. **SPECTACLE BY DEFAULT — dramatize for visual richness.** This is YouTube
   entertainment. Build cinematic, layered compositions: action/combat, spell-duels
   (đấu pháp), daoist magic, multi-character framing, wide map-scale landscape,
   crowds/factions, foreground/midground/background depth. You are ALLOWED to
   amplify beyond the literal chapter — add supporting characters, vistas, and
   dramatic energy — as long as it stays genre-consistent (xianxia stays xianxia),
   identity-consistent (verbatim bible anchor for named chars; freely add UNNAMED
   groups), and does not contradict stated plot facts. NEVER default to a lone
   protagonist standing or gazing. (If `mode = faithful` is passed, do not invent
   combat/crowds absent from the chapter — render only what the text supports, but
   still richly composed.)

## SUBJECT = THIS SCENE'S CHARACTERS ONLY (no global hero-lock)
The Subject characters are EXACTLY `scene_row.characters` for this scene — no more,
no less. If the protagonist is NOT in `scene_row.characters`, do NOT insert them.
NEVER apply a blanket "every image features the protagonist" template — that is the
exact monotony failure this skill forbids. When the row lists multiple characters or
a group, frame them ALL, not just the most important one.

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

Story DNA: ...

Setting: ...

Composition: ...

Subject: <verbatim anchor> ... <scene state>

Action / Energy: ...

Style: ...

Lighting / Color: ...

Atmosphere: ...

Negative: ...
```

(If `has_video: true`, the `## Video Prompt` section will be appended by
`prompt-expander-video.md` in a separate call.)

## MANDATORY SELF-CHECK BEFORE WRITE

1. **Identity Anchor verbatim check** — for each character mentioned in
   Subject, copy their full anchor from the bible char-by-char. Compare
   to what you wrote in Subject. If even one character differs (synonym,
   punctuation, capitalization) → REGENERATE the Subject.
2. **Word count check** — count words in the prompt body. If >650 → trim
   Setting and Style first. If <350 → expand Story DNA, Composition, Lighting,
   and Atmosphere with concrete scene facts.
3. **Negative count check** — 28 items max (10+5+5+4+4), comma-separated. The last
   4 are the style negatives from `.work/active-style.md`.
4. **Safety check** — no copied web image, famous face, celebrity likeness,
   known-character likeness, exact branded costume, or living-artist mimicry.
5. **Depth check** — prompt has foreground/midground/background, at least 3
   environment layers, concrete light direction, and scene-specific action or
   energy, AT LEAST as rich as the template `IMAGE EXAMPLE`. If the scene supports
   multiple actors but Subject/Composition is solo-only → REGENERATE.
6. **All sections present** with exact headers `Camera:`, `Story DNA:`,
   `Setting:`, `Composition:`, `Subject:`, `Action / Energy:`, `Style:`,
   `Lighting / Color:`, `Atmosphere:`, `Negative:`.
7. **No-boilerplate check** — `Setting`, `Composition`, and `Atmosphere` MUST be
   specific to THIS scene's chapter excerpt and shot. Do NOT paste an identical
   paragraph reused across scenes. If your Setting/Composition/Atmosphere could be
   dropped unchanged into a different scene → REWRITE with this scene's concrete
   location, layout, characters, and action.
8. **Subject scope check** — Subject contains exactly `scene_row.characters`. If you
   added the protagonist to a scene that did not list them → REGENERATE.

## STDOUT SUMMARY
```
Scene <NNN> image written: <wc> words, anchor verified for <N> chars
```
