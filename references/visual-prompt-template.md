# Visual Prompt Template — Master Format Spec

> Related: [[genre-keywords]] · [[identity-anchor-rules]] · [[scene-tag-camera-mapping]] · [[negative-lists]] · [[youtube-pacing-guide]]

This is the canonical format spec the LLM must follow when expanding scenes.
Two formats: **Image** (deep 350–550 words, sectioned) and **Video**
(deep Veo3 5-part formula).

## DEEP PROMPT DNA — MANDATORY

Every prompt must be dense with scene-specific information. Borrow the structure
discipline of a production master prompt: story DNA, identity locks, signature
props, layered background, color DNA, camera language, lighting, action/energy,
audio when relevant, and explicit negatives.

Never output a shallow prompt such as "wide shot, ancient room, cinematic,
beautiful." **Grounded visual specificity is the default** — actively build:
- foreground / midground / background composition
- exactly the participants and groups supported by the source
- source-supported geography, architecture, landscape, action, ritual, or stillness
- concrete costume, weapon, prop, terrain, weather, particles, and light direction
  only when established by the chapter or identity bible

Scene diversity must be plot-fit, not templated. Across a run, prompts should vary
through truthful camera placement, composition, visible action phase, focus,
lighting, palette, texture, and atmosphere according to each chapter's actual
narrative beat. Do not spotlight the protagonist by default.

You may not dramatize beyond the QA'd chapter. Do not add characters, crowds,
combat, locations, props, powers, weather, injuries, or outcomes. Read and obey
`strict-generation-contract.md`.

Safety & Compliance (8 blocked categories — enforced by the content-safety gate,
see [[blocklist-content-safety]]):
1. **Brand / logo / trademark** — no named brands (Nike, Apple, Gucci, …).
2. **Real public figures** — no celebrity/actor faces or "looks like <real
   person>" likeness; use the bible's original faces.
3. **Copyrighted IP characters** — no Naruto/Pikachu/Elsa-style known characters.
4. **Copyrighted images/artworks** — no copying a web image, thumbnail, poster,
   frame, composition, or living-artist imitation.
5. **Excessive gore** — combat / đấu pháp / stylized light blood OK; no
   decapitation, disembowelment, gushing blood, or torture.
6. **Sexual / nudity** — keep characters modestly clothed; no suggestive exposure.
7. **Religious disrespect** — fictional cultivation imagery (tu tiên, đạo sĩ,
   Daoist/Buddhist temples) is fine; do NOT depict/desecrate REAL religion.
8. **Live-action VIDEO** — video prompts must be the chosen animated/illustrated
   style; no live-action, photoreal footage, or real-human likeness. (Painterly
   "semi-realistic" catalog styles are still allowed — the ban targets live-action
   realism, not painterly art.)

Use original descriptive style vocabulary from `.work/active-style.md`.

---

## IMAGE PROMPT FORMAT

**Target length:** 350–550 words total. Hard penalty if >650.

**Sections (must appear in this exact order, with these exact headers):**

```
Camera: <fresh shot type, lens mm, angle, framing chosen for this beat>
Story DNA: <source-supported narrative and emotional beat; omit unstated conflict or lore>
Setting: <source-supported location/layout/time/weather; omit facts the source does not establish>
Composition: <foreground / midground / background using supported elements or negative space>
Subject: <listed character anchors, or the row's environment/object focus when no character is listed>
Action / Energy: <source-supported action, gesture, environmental motion, or truthful stillness>
Style: <Style block from .work/active-style.md using original descriptors, aspect ratio 16:9>
Lighting / Color: <supported source light, or restrained neutral rendering without a time/weather claim>
Atmosphere: <supported particles/weather/reaction, or stillness, depth, contrast, and negative space>
Negative: <anti-Western + genre + AI-defense + likeness/copyright + style negatives — max 28 items>
```

**Rules:**
- When `scene_row.characters` is non-empty, Subject MUST start with each listed
  character's verbatim Identity Anchor block from the bible (see
  [[identity-anchor-rules]]). Do not paraphrase. When it is empty, do not insert a
  person; use the grounded environment/object focus.
- Style section uses the `Style block` of the chosen style in `.work/active-style.md`.
  Do not add named IP/artist/celebrity references. The selected style
  (see [[style-catalog]]) decides the look through descriptive vocabulary.
- Aspect ratio 16:9 (YouTube native).
- Use English visual vocabulary; map VN genre words via [[genre-keywords]].

### IMAGE FORMAT EXAMPLE — STRUCTURE ONLY, NEVER A CONTENT DEFAULT

*(Every positive fact below is synthetic. It is forbidden in an actual scene
unless that scene's QA chapter independently supports it. Do not copy its camera,
weather, cast size, action, palette, props, layer count, or sentence rhythm.)*

```
Camera: medium-wide shot, 35mm lens, low three-quarter angle, 16:9 frame,
foreground weapon arc crossing the lower left, deep focus so the battlefield scale
stays readable behind the main figures.

Story DNA: late-dynasty cultivation war at the edge of a mountain pass; a ruined
sect convoy is being overrun while the protagonist chooses to reveal forbidden
body-tempering power before the enemy formation closes.

Setting: broken stone road above a gorge at stormy dawn, cliffside watchtowers,
tilted war banners, wet pine forest on both ridges, rainwater running through
wheel ruts, distant fortress gate half-hidden by blue-grey mist.

Composition: foreground splinters, mud spray, and a fallen bronze shield;
midground protagonist and two allies bracing against three masked cultivators;
background shows a wide map-scale valley with retreating civilians, torch lines,
and a circular talisman formation glowing across the pass.

Subject: Trương Tiểu Phàm — 22 years old, tall lean build, shoulder-length jet-black
hair tied with a single white silk ribbon, angular jaw, narrow sharp obsidian eyes,
small jade pendant carved with lotus motif at the throat, ash-grey hemp robe with
indigo trim, hand resting on the hilt of a slim straight jian sword. Robe soaked
at the hem, cheek cut by rain, stance lowered, left hand shielding a wounded ally
while the right hand draws the sword half free.

Action / Energy: silver sword-light curves outward like a crescent, colliding
with three red talisman chains; sparks scatter into rain, the stone road cracks
under foot pressure, sleeves and banners whip in the same wind direction.

Style: cinematic painterly realism, restrained brush texture over realistic
anatomy, ancient Chinese fantasy production design, muted ink-wash depth,
selective jade-green and silver-grey accents, soft film grain, 16:9 aspect ratio.

Lighting / Color: cold blue storm fill from the left, thin warm dawn rim from
behind the fortress wall, jade talisman glow underlighting wet faces and sword
edges, lifted shadows with no pure black, color temperature 4200K key + 7000K fill.

Atmosphere: rain streaks, steam rising from cracked stones, torn paper talismans
spinning, drifting pine needles, distant soldiers blurred by mist, all motion
leaning diagonally to reinforce the gale.

Negative: no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair, no blue eyes default, no jeans, no sneakers, no glasses, no neon,
no logo, no watermark, no text overlay, no distorted hands, no extra fingers,
no copied web image, no real public figure or celebrity face, no copyrighted
character likeness, no brand logo or trademark, no nudity or suggestive exposure,
no graphic gore or blood splatter, no photographic skin pores on close-ups.
```

---

## VIDEO PROMPT FORMAT (Google Veo3 — official 5-part)

**Target length:** ~400–600 words, **HARD CAP 3800 characters** (Google Flow /
Veo3 rejects prompts over 4000 chars; 3800 leaves margin). The char cap is the
binding limit — replaces the old 900-word cap. Trim order if over: Context detail
first, then Style detail; never drop a beat or shorten the Identity Anchor.
**Hard duration cap:** 8 seconds total (Veo3 limit). Max 3 timestamped beats.

**Sections (must appear in this exact order, with these exact headers):**

```
Cinematography: <shot type, lens, camera movement, framing, aspect ratio>
Subject: <PASTE IDENTITY ANCHOR VERBATIM, then current state/wardrobe specifics for the shot>
Action: <2-3 timestamped beats using ms-precision tags [00:00-00:02.5]>
Context: <source-supported location, time, weather, era markers, and elements>
Style & Ambiance: <Style block from .work/active-style.md, color palette, lighting, safety negatives, AND audio cue embedded as one of the ambiance layers — NOT as a tag at the end>
```

**Audio rule (critical):** Audio is part of *Style & Ambiance*, written as
diegetic + ambient layer. Example: `Audio: steel ringing on steel, low wind
through bamboo, distant temple bell.` NEVER append `[audio: ...]` at the end.

### VIDEO FORMAT EXAMPLE — STRUCTURE ONLY, NEVER A CONTENT DEFAULT

*(Every positive fact below is synthetic and forbidden unless independently
supported by the current QA chapter. Do not reuse its motion, weather, camera,
palette, objects, audio, or beat progression.)*

```
Cinematography: medium-wide tracking shot, 35mm lens, handheld follow-cam with
subtle motion blur on quick movements, 16:9 aspect ratio, eye-level then tilting
to slight low-angle on the third beat.

Subject: Trương Tiểu Phàm — 22 years old, tall lean build, shoulder-length jet-black
hair tied with a single white silk ribbon, angular jaw, narrow sharp obsidian eyes,
small jade pendant carved with lotus motif at the throat, ash-grey hemp robe with
indigo trim, hand resting on the hilt of a slim straight jian sword. Robe hem is
mud-streaked from days of travel; ribbon is slightly loose.

Action:
[00:00-00:02.5] He steps onto a moss-covered stone bridge, robe trailing in slow
wind, gaze fixed forward; one hand drifts to the sword hilt.
[00:02.5-00:05.0] Mid-bridge, he halts — head turning sharply over his right
shoulder, hair whipping across his cheek; eyes narrow.
[00:05.0-00:08.0] He pivots fully, draws the jian halfway from its sheath with a
single fluid motion; camera tilts to low angle, framing him against the gathering
storm clouds behind.

Context: ancient Tang-era stone bridge over a black-water gorge, bamboo forest
on both banks bending in pre-storm gusts, mid-afternoon overcast light, jade-green
moss and lichen on the stones, faint mist rising from the gorge below.

Style & Ambiance: cinematic painterly realism with ancient Chinese fantasy
production design, muted desaturated palette with jade-green and silver-grey
accents, soft diffused key light from above-camera, cool blue fill, volumetric
atmosphere with light god-rays; avoid copied web images, famous faces, branded
costumes, and known-character likenesses. Audio: low wooden creak of the bridge,
bamboo leaves rustling in rising wind, distant rumble of thunder, sword ringing
faintly as it slides half-out of the lacquered sheath, no music.
```

---

## PER-PLATFORM TWEAKS (paste-time hints — do NOT include in prompt body)

| Tool | Tip |
|---|---|
| Image tools | Paste full image block; "16:9" should be included. |
| Qwen-Image | Same; supports CN/EN mixed prompts. |
| ChatGPT (DALL-E) | Drop the `Negative:` line — DALL-E ignores it; convert to "avoid X, X" inline in Style. |
| Veo3 | Paste full video block; respects ms-timestamps; honors Audio: inline. |
| Seedance | Paste video block; may truncate at 600 words — trim Context if needed. |
