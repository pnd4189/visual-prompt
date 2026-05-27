# Visual Prompt Template — Master Format Spec

> Related: [[genre-keywords]] · [[identity-anchor-rules]] · [[scene-tag-camera-mapping]] · [[negative-lists]] · [[youtube-pacing-guide]]

This is the canonical format spec the LLM must follow when expanding scenes.
Two formats: **Image** (hybrid 200–300 words, sectioned) and **Video**
(Google Veo3 official 5-part formula).

---

## IMAGE PROMPT FORMAT

**Target length:** 200–300 words total. Hard penalty if >320.

**Sections (must appear in this exact order, with these exact headers):**

```
Camera: <shot type, lens mm, angle, framing>
Setting: <location, time of day, weather, atmosphere, era markers>
Subject: <PASTE IDENTITY ANCHOR VERBATIM from character-bible.md, then pose, expression, props>
Style: <Style block from .work/active-style.md + its reference anchors, aspect ratio 16:9>
Lighting: <key light, fill, rim, mood, color temperature>
Negative: <anti-Western + genre + AI-defense + style negatives — max 24 items, comma-separated>
```

**Rules:**
- Subject section MUST start with the verbatim Identity Anchor block from
  the bible (see [[identity-anchor-rules]]). Do not paraphrase.
- Style section uses the `Style block` of the chosen style in `.work/active-style.md`
  and cites its `reference anchors`. There is NO global cinema reference — the
  selected style (see [[style-catalog]]) decides the look.
- Aspect ratio 16:9 (YouTube native).
- Use English visual vocabulary; map VN genre words via [[genre-keywords]].

### IMAGE EXAMPLE — ADAPT TO SCENE, DO NOT COPY VERBATIM

*(Example shown for style `painterly-realism-cinematic`. With another style, the
Style line comes from that style's `Style block` and the Negative gains its 4 style
negatives for 24 total. See [[style-catalog]].)*

```
Camera: medium shot, 50mm lens, eye-level, centered framing, shallow depth of field.

Setting: stone-tiled mountain summit at dawn, ancient pine trees twisted by wind,
mist drifting between cliff faces, distant peaks silhouetted in violet-blue,
Tang dynasty era markers (carved stone lanterns, jade incense burner).

Subject: Trương Tiểu Phàm — 22 years old, tall lean build, shoulder-length jet-black
hair tied with a single white silk ribbon, angular jaw, narrow sharp obsidian eyes,
small jade pendant carved with lotus motif at the throat, ash-grey hemp robe with
indigo trim, hand resting on the hilt of a slim straight jian sword. Standing in
half-profile, gazing toward the eastern horizon, lips slightly parted, breath
visible in cold air.

Style: cinematic 4K, painterly realism in the visual language of Crouching Tiger
Hidden Dragon (2000), muted desaturated palette with selective jade-green and
silver-grey accents, ink-wash background suggestion, 16:9 aspect ratio.

Lighting: golden hour key light from camera-right casting long warm rim on hair
and shoulders, cool blue fill from camera-left, soft volumetric god-rays through
mist, color temperature 4200K key + 7000K fill.

Negative: no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair, no blue eyes default, no jeans, no sneakers, no glasses, no neon,
no logo, no watermark, no text overlay, no distorted hands, no extra fingers,
no photographic skin pores on close-ups (painterly skin only).
```

---

## VIDEO PROMPT FORMAT (Google Veo3 — official 5-part)

**Target length:** 400–800 words. Hard cap 800.
**Hard duration cap:** 8 seconds total (Veo3 limit). Max 3 timestamped beats.

**Sections (must appear in this exact order, with these exact headers):**

```
Cinematography: <shot type, lens, camera movement, framing, aspect ratio>
Subject: <PASTE IDENTITY ANCHOR VERBATIM, then current state/wardrobe specifics for the shot>
Action: <2-3 timestamped beats using ms-precision tags [00:00-00:02.5]>
Context: <location, time of day, weather, era markers, supporting elements>
Style & Ambiance: <Style block + reference anchors from .work/active-style.md, color palette, lighting, AND audio cue embedded as one of the ambiance layers — NOT as a tag at the end>
```

**Audio rule (critical):** Audio is part of *Style & Ambiance*, written as
diegetic + ambient layer. Example: `Audio: steel ringing on steel, low wind
through bamboo, distant temple bell.` NEVER append `[audio: ...]` at the end.

### VIDEO EXAMPLE — ADAPT TO SCENE, DO NOT COPY VERBATIM

*(Example shown for style `painterly-realism-cinematic`. With another style, the
Style & Ambiance line comes from that style's `Style block` + reference anchors.
See [[style-catalog]].)*

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

Style & Ambiance: cinematic 4K in the visual language of Crouching Tiger Hidden
Dragon (2000), painterly realism, muted desaturated palette with jade-green and
silver-grey accents, soft diffused key light from above-camera, cool blue fill,
volumetric atmosphere with light god-rays. Audio: low wooden creak of the bridge,
bamboo leaves rustling in rising wind, distant rumble of thunder, sword ringing
faintly as it slides half-out of the lacquered sheath, no music.
```

---

## PER-PLATFORM TWEAKS (paste-time hints — do NOT include in prompt body)

| Tool | Tip |
|---|---|
| Gemini Imagen | Paste full image block; "16:9" honored. |
| Qwen-Image | Same; supports CN/EN mixed prompts. |
| ChatGPT (DALL-E) | Drop the `Negative:` line — DALL-E ignores it; convert to "avoid X, X" inline in Style. |
| Veo3 | Paste full video block; respects ms-timestamps; honors Audio: inline. |
| Seedance | Paste video block; may truncate at 600 words — trim Context if needed. |
