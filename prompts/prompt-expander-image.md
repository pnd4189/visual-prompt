# Image Prompt Expander — Per Scene

## ROLE
Expand one scene row from the scene-plan into a full image prompt block,
matching the format spec in `@references/visual-prompt-template.md` exactly.

## INPUT (per scene)
- `scene_row` — `{scene_id, chapter, source_anchor, scene_tag, characters,
  synopsis, setting_plan, camera_plan, action_plan, palette_plan, ...}`
- `bible` — `character-bible.md` content (filter to characters in this scene)
- `genre` — detected genre keyword
- `mode` — `grounded` (required)
- `chapter_excerpt` — the relevant chapter text ONLY (NOT full chapters.json)
- `active_style` — `.work/active-style.md` content (one chosen style entry)
- `cache_key` — SHA1(input.hash + bible.hash + plan.hash + style.hash + scene_row_text)

## CRITICAL — CHAPTER EXCERPT RULE
Load ONLY the chapter referenced by `scene_row.chapter`. Do NOT load
`chapters.json` whole — for 18k-word files, that blows the context.

## SOURCE-GROUNDING RULE (hard)

Read `@references/strict-generation-contract.md`. The QA chapter and bible are
the only sources of story facts. Verify that `scene_row.source_anchor` is a
contiguous excerpt of the loaded chapter before writing. Story DNA, Setting,
Subject, and Action may describe only facts supported by that chapter, the anchor,
and the listed bible identities.

Do not add unnamed supporting characters, crowds, enemies, creatures, weapons,
artifacts, locations, weather, injuries, magic, dialogue outcomes, or aftermath
that the source does not establish. If a detail is unknown, omit it. Creative
variation belongs in camera, composition, focus, light, palette, texture, and
atmosphere — never in new plot facts.

## TASK
1. Load `@references/visual-prompt-template.md` (image format section) AND
   `.work/active-style.md` (the chosen style entry). The `Style block` field of
   active-style is the Style section base; use its descriptive style vocabulary.
   The synthetic `IMAGE FORMAT EXAMPLE` demonstrates section syntax only. It is
   not a content, camera, action, layer, palette, or sentence template. Never
   borrow a detail from it unless the current QA chapter independently supports
   that detail.
2. Load `@references/scene-tag-camera-mapping.md` — pick row matching
   `scene_row.scene_tag` for Camera defaults.
3. Load `@references/negative-lists.md` — compose 5-layer negative (universal
   anti-Western + genre + AI-defense + safety/compliance + style negatives), cap 28 items
   (8+5+5+6+4). Layer 5 = first 4 items from the `style negatives` field of `.work/active-style.md`.
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
7. **SAFETY RULE (hard, applies to ALL sections — not just Style).** The prompt
   must avoid copyright + platform-policy + religious-sensitivity violations:
   - **No brand / logo / trademark names** in any positive section (Nike, Apple,
     Gucci, Coca-Cola, …) — describe generic objects instead.
   - **No real public figures / celebrity / actor names or "looks like / in the
     style of / giống <real person>"** likeness. Use the bible's original faces.
   - **No copyrighted IP characters** (Naruto, Pikachu, Iron Man, Elsa, …) or
     exact branded/IP costumes; the chosen style decides the look through original
     descriptors.
   - **No sexual / nudity** content (no nudity, topless, lingerie, suggestive
     exposure) — keep characters modestly clothed.
   - **No EXCESSIVE gore** (decapitation, disembowelment, gushing blood, torture).
     Combat / đấu pháp / stylized light blood stay ALLOWED — only graphic gore is
     blocked.
   - **Respect real religion.** Genre-native fictional cultivation imagery (tu
     tiên, đạo sĩ, chùa, Daoist/Buddhist temples) is fine; do NOT depict, insult,
     or desecrate REAL religion (real prophets/deities, sacred symbol + gore/nudity).
   - If the chapter content itself is forbidden (e.g. explicit sexual or
     gratuitously gory passage), **abstract it** into a non-graphic composition.
8. **GROUNDED CREATIVE REALIZATION.** Build a layered composition from the actual
   beat and the four plans in `scene_row`. Vary shot scale, camera height/lens,
   focus, foreground/midground/background, lighting direction, palette, texture,
   and atmosphere. These choices must not add a story fact. Never use a canned hero
   template, and never add a character simply to make the frame cinematic.
9. **PLOT-FIT VARIATION.** Honor exactly `scene_row.characters`, setting, and action.
   If the row is an environment, object, aftermath, or quiet emotional beat, keep
   that focus. A scene can be visually distinctive without inventing an event.

## HARD CROSS-SCENE UNIQUENESS

- Do not reuse an exact sentence or phrase longer than 8 words from any other
  scene in this run. The only exceptions are the verbatim Subject identity
  anchor, the selected Style block, and the shared Negative requirements.
- Choose Camera from this scene's visible beat. Do not rotate through or lightly
  paraphrase a stock camera sentence across scenes.
- Story DNA and Atmosphere must express the changing energy of this exact moment,
  not a static chapter summary shared by several scenes.
- The active parent model writes this scene directly. Never delegate it or use a
  scripted template factory.

## FORBIDDEN ANTI-PATTERNS (hard reject — regenerate if any appear)

These are the exact failure modes observed in production. If your output
contains ANY of these, STOP and rewrite the offending section:

1. **Synopsis copy-paste into Story DNA.** Story DNA must be a 2-3 sentence
   source-grounded description of this plot beat — NOT the synopsis repeated
   verbatim with boilerplate padding. Mention motivations, conflict, cultivation
   logic, or emotion only when the chapter states or directly demonstrates them.
2. **Truncated text fragments.** Never write `"engaged in the action described:
   across the river from the mark..."` or any truncated reference. Write the
   full, concrete description.
3. **Generic template phrases.** Never write `"era-appropriate architecture"`,
   `"the scene captures the essence"`, `"Every element from the folds in the
   clothing to the subtle micro-expressions"`, `"ensuring absolute continuity"`,
   or similar boilerplate padding. Replace them only with details supported by
   the chapter. If the source does not name a material, terrain, or weather
   condition, omit it instead of guessing.
4. **Placeholder settings.** Never write `"the setting described: [copy of
   synopsis]"`. Setting must name the actual supported location and layout. Use
   only physical details present in the chapter; negative space, occlusion, and
   framing may provide depth without inventing furniture, weather, or time of day.
5. **Generic lighting.** Never write `"Color temperature aligns with the mood"`.
   Name a specific light source only when supported. Otherwise use restrained
   neutral illumination, direction, contrast, and shadow behavior without
   claiming a canonical time, lamp, moon, fire, or magical glow.
6. **Generic atmosphere.** Never write `"specific particles related to [synopsis
   fragment]"`. Name particles or weather only when the source supports them.
   Otherwise create atmosphere through stillness, depth falloff, negative space,
   material contrast, and source-supported environmental motion.
7. **Lazy composition.** Never write only `"Rule of thirds applied"` or
   `"Dynamic framing"`. Name 2-3 specific objects in foreground, midground, and
   background.

## INLINE STRUCTURE EXAMPLE (syntax only — never reuse its content or pattern)

```
Camera: extreme wide shot, 24mm lens, slow push-in framing, 16:9 frame, deep
focus keeping both the foreground cauldron smoke and the far chamber walls
razor-sharp.

Story DNA: opening beat of chapter 301 — Lâm Ý has begun his forbidden
body-tempering experiment with ancient cinnabar-mercury dan medicine inside a
sealed underground chamber. Tề Châu Cơ lingers at the doorway, torn between
curiosity and concern for his friend. The tension is alchemical — one wrong
pulse of qi and the cauldron explodes.

Setting: deep underground stone chamber beneath a military compound in Lô Châu,
rough-hewn granite walls stained with centuries of mineral residue, a single
ancient bronze cauldron at center with hairline cracks glowing faint crimson,
stone floor covered in chalked talisman circles now half-erased by foot traffic,
no windows — only a narrow stone archway leading to a corridor lit by a distant
oil lamp.

Composition: foreground — wisps of crimson medicinal vapor curling upward from
the cauldron's mouth, brass ladle resting on the rim catching the glow;
midground — Lâm Ý seated cross-legged on a stone platform directly behind the
cauldron, Tề Châu Cơ's silhouette visible in the doorway arch to the right;
background — chamber recedes into shadow with rough tool marks on the walls, a
wooden rack of ceramic herb jars barely visible, iron chains hanging from
ceiling hooks.

Subject: Lâm Ý — 16-17 years old, tall, muscular, powerful frame, short
cropped black hair slightly unruly, sharp angular jaw, deep-set intense dark
eyes with cunning glint, wears Thiên Tích Bảo Y inner armor beneath his
ash-grey hemp training robe with sleeves rolled to forearms, Hồng Long Ngân Sa
jade-red bracelets on both wrists. Currently seated in lotus position, eyes
closed, veins at his temples darkening as cinnabar particles circulate, fists
clenched on his knees, a thin sheen of sweat on his forehead.

Action / Energy: static ritual tension — no visible motion except the slow curl
of crimson vapor, but the chamber stones vibrate subtly (visible as fine dust
motes trembling in the air), Lâm Ý's wrist bracelets emit a faint jade-red
pulse synchronized with his heartbeat, the talisman chalk lines on the floor
glow intermittently.

Style: high-end Chinese 3D cultivation donghua render, cel-shaded characters
with soft subsurface skin, physically-based cloth on flowing silk robes,
volumetric qi mist, saturated cinematic key light, clean rim lighting, original
character faces, 16:9 aspect ratio.

Lighting / Color: deep warm amber key light from the cauldron's crimson glow
reflecting upward onto Lâm Ý's face and the ceiling, cool blue-grey fill from
the corridor behind Tề Châu Cơ creating a temperature split, jade-red rim light
on Lâm Ý's bracelets, lifted shadows in the chamber corners with no pure black,
overall palette: crimson-amber core fading to indigo-grey edges.

Atmosphere: thick medicinal vapor with visible particulate density near the
cauldron thinning toward the edges, fine stone dust suspended in still air
catching the crimson light, the silence is oppressive — conveyed by the absolute
stillness of every fabric fold and the undisturbed chalk circles on the floor.

Negative: no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair as default, no blue eyes as default, no Renaissance fair costume,
no fur cloaks, no Viking horns, no jeans, no sneakers, no glasses, no neon
lighting, no automatic firearms, no logo, no watermark, no text overlay, no
distorted hands, no extra fingers, no copied web image, no real public figure
or celebrity face, no copyrighted character likeness, no brand logo or trademark,
no nudity or suggestive exposure, no graphic gore or blood splatter, no
live-action photographic skin, no muted live-action desaturation, no Western 3D
cartoon proportions, no claymation
```

**Do not imitate this example.** It is a syntax sample, not a reusable creative
pattern. Richness must come from the current chapter plus non-canonical rendering
choices such as camera, focus, composition, contrast, and palette. An empty layer
or negative space is valid. Never add an object, person, weather condition, magic
effect, or action merely to reach a line or word target.

## SUBJECT = THIS SCENE'S CHARACTERS ONLY (no global hero-lock)
The Subject characters are EXACTLY `scene_row.characters` for this scene — no more,
no less. If the protagonist is NOT in `scene_row.characters`, do NOT insert them.
NEVER apply a blanket "every image features the protagonist" template — that is the
exact monotony failure this skill forbids. When the row lists multiple characters or
a group, frame them ALL, not just the most important one.
If the row focuses on environment, artifact, chưởng lực, crowd, army, faction, or
aftermath, the Subject/Composition must make that focus primary instead of turning
it into a protagonist portrait.

## IDENTITY ANCHOR — VERBATIM, NOT PARAPHRASE
For each character in `scene_row.characters`:
1. Find their row in the bible.
2. Concatenate fields per `@references/identity-anchor-rules.md` Identity
   Anchor Block format.
3. Paste that EXACT string into Subject section. Do not change a single
   word, even if the chapter describes them slightly differently.
4. After the verbatim block, append only scene-specific pose, expression, or
   wardrobe condition supported by this chapter.

## OUTPUT
Write `.work/scene-<NNN>.md` (NNN = zero-padded `scene_row.scene_id`):

```markdown
---
scene_id: <NNN>
cache_key: <sha1>
source_anchor: <exact source_anchor from scene_row>
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
   Setting and Style first. If <350, expand camera, composition, focus, neutral
   lighting treatment, palette relationships, and supported scene facts. If the
   floor cannot be reached without inventing canon, HALT instead of padding.
3. **Negative count check** — 28 items max (8+5+5+6+4), comma-separated. The last
   4 are the style negatives from `.work/active-style.md`.
4. **Safety check (categories 1–7)** — scan EVERY positive section, not just
   Style: no brand/logo/trademark name; no real public figure / celebrity /
   "looks like <real person>" likeness; no copyrighted IP character or exact
   branded costume; no copied web image or living-artist mimicry; no nudity /
   sexual exposure (keep modestly clothed); no excessive gore (combat OK, graphic
   gore not); respect real religion (fictional cultivation imagery allowed). If any
   appears → REWRITE the offending span to a generic/abstract equivalent.
5. **Depth check** — prompt distinguishes foreground/midground/background (a layer
   may be negative space), concrete light direction, and the scene's supported
   action, environmental motion, or stillness. If the scene supports multiple
   actors but Subject/Composition is solo-only → REGENERATE.
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
9. **Plot-fit diversity check** — If this prompt could be reused for another
   chapter by only swapping a name, or if it ignores the scene tag's landscape /
   combat / group / artifact focus, REGENERATE with concrete story-specific
   staging.
10. **Grounding check** — every named participant, location, object, action, and
    outcome must be traceable to the loaded chapter/bible. Remove unsupported
    embellishment before saving.
11. **Cross-scene phrase check** — compare every section except Subject anchor,
    Style, and Negative with scenes already written in this batch. If an exact
    sentence or phrase longer than 8 words repeats, REWRITE it before saving.
12. **Artifact anchor check** — frontmatter `source_anchor` is the exact
    `scene_row.source_anchor`; do not paraphrase, shorten, or replace it.

## STDOUT SUMMARY
```
Scene <NNN> image written: <wc> words, anchor verified for <N> chars
```

---

## LEAN SPEC (chỉ khi run có cờ `--lean`)

Mục tiêu khác hẳn deep spec: **prompt ngắn, sinh nhanh, khác nhau thật**. Máy quay,
ánh sáng, bố cục, không khí — để model sinh ảnh tự quyết. Bạn chỉ khoá 3 thứ nó
không thể tự suy ra: **ai đang trên khung hình, ở đâu, đang làm gì**.

Đúng 5 mục, không thêm mục nào:

```markdown
## Image Prompt

Subject: <nhận dạng nhân vật NGUYÊN VĂN từ character bible — tên, tuổi, dáng,
  trang phục, đặc điểm nhận dạng. Cảnh không người thì tả vật/công trình chính>

Setting: <nơi chốn cụ thể của ĐÚNG khoảnh khắc này, 8-20 từ>

Action: <điều đang xảy ra tại `source_anchor`, 8-20 từ, động từ cụ thể>

Style: <style id của series, nguyên văn — giống nhau ở mọi cảnh>

Negative: <danh sách an toàn — giống nhau ở mọi cảnh>
```

Tổng thân prompt 60-220 từ. Ngắn hơn không có nghĩa là mờ nhạt:

- `Subject` và `Style` LẶP LẠI giữa các cảnh là đúng thiết kế — đó là thứ giữ nhân
  vật và phong cách nhất quán. Gate không so trùng hai mục này.
- `Setting` và `Action` PHẢI khác nhau ở từng cảnh — gate so trùng đúng hai mục
  này. Chép lại từ cảnh trước là hỏng.
- Hai mục đó CÒN bị đo độ dài: dưới 8 từ là FAIL ngay ở batch đầu (trần 40 từ
  chỉ chặn trường hợp một mục nuốt cả prompt). Viết `Setting: living room` là sai — phải tả đúng nơi chốn của khoảnh
  khắc này. Mục cụt vừa vô nghĩa với model sinh ảnh, vừa ép các cảnh trùng nhau.
- Mỗi `Action` bám vào `source_anchor` riêng của hàng scene-plan. Anchor đã khác
  nhau 100% giữa các cảnh, nên nếu bạn viết đúng khoảnh khắc đó thì `Action` tự
  khác nhau — không cần bịa thêm.
- Cấm dựng sẵn vài biến thể rồi rải đều. Đó là dán khuôn, gate bắt được.
