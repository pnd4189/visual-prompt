# Style Catalog — 18 Art Styles for Chinese Web-Novel Visuals

> Related: [[genre-style-recommendation]] · [[visual-prompt-template]] · [[negative-lists]] · [[music-mood-mapping]]

Single source of truth for the multi-style system. One entry = one art style.
The chosen style is materialized verbatim into `.work/active-style.md` (one entry),
then consumed by the image/video expanders and the music builder.

**`id` is kebab-case and stable** — it is the `--style <id>` value and feeds the
scene cache key. Do not rename ids without busting caches.

Categories:
- **narrative-safe** — holds character identity well across many scenes; safe for
  full image+video pipeline.
- **accent-title-card** — strong look but weak at keeping the same face/body across
  shots; best for opening title cards / montages, not every scene.
- **video-oriented** — designed for motion; still frames look incomplete.

---

## Quick reference (id → category)

| id | category | one-line |
|---|---|---|
| `donghua-xianxia` | narrative-safe | 3D cultivation donghua, glossy cel-lit immortal world |
| `painterly-realism-cinematic` | narrative-safe | cinematic 4K painterly realism (v0.2 default look) |
| `semi-realistic-digital-painting` | narrative-safe | textured-brush semi-realistic digital painting |
| `light-novel-moe` | narrative-safe | soft anime light-novel aesthetic, clean moe shading |
| `concept-art-cityscape` | narrative-safe | matte-painting environment / vista concept art |
| `dark-fantasy-modao` | narrative-safe | brooding 2D/3D-hybrid demonic-cultivation donghua |
| `game-cg-25d` | narrative-safe | polished cel-shaded 2.5D game CG |
| `dark-zhiguai-folk-horror` | narrative-safe | eerie folk-tale horror, muted ominous palette |
| `scifi-donghua-kehuan` | narrative-safe | Chinese sci-fi (kehuan) hard-surface + neon |
| `manhua` | narrative-safe | clean-line Chinese webcomic / manhua flats |
| `ink-wash-stylized` | accent-title-card | stylized still shuimo ink-wash brushwork |
| `flat-poster-silhouette` | accent-title-card | flat color-block silhouette poster art |
| `traditional-pattern-minimal` | accent-title-card | decorative motif + negative space minimal |
| `watercolor-gouache` | accent-title-card | soft watercolor / gouache wash illustration |
| `minimalist-calligraphy-symbolic` | accent-title-card | calligraphy + symbol, heavy negative space |
| `folk-nianhua` | accent-title-card | New Year woodblock-print folk art |
| `photobash-epic-poster` | accent-title-card | photobashed epic film key-art |
| `ink-wash-animation` | video-oriented | moving traditional ink-wash animation |

---

## Entries

### donghua-xianxia — Tiên hiệp Donghua / Chinese 3D cultivation donghua
- category: narrative-safe
- best-fit genres: tiên hiệp, huyền huyễn
- description: Glossy 3D-rendered cultivation world with cel-lit characters,
  flowing robes, floating sect architecture and qi effects — the modern donghua look.
- style descriptors: high-end Chinese 3D cultivation donghua, glossy cel-lit
  characters, floating sect architecture, qi mist, flowing robe physics.
- Style block (EN, paste-ready): high-end Chinese 3D cultivation donghua render,
  cel-shaded characters with soft subsurface skin, physically-based cloth on flowing
  silk robes, volumetric qi mist, saturated cinematic key light, clean rim lighting,
  original character faces, 16:9 aspect ratio.
- palette: jade-green, cyan qi glow, warm gold highlights, deep indigo shadow
- style negatives: no live-action photographic skin, no muted live-action desaturation, no Western 3D cartoon proportions, no claymation
- music/score anchor: synth-orchestral donghua hybrid — Chinese ethnic instruments (guzheng, dizi) over modern cinematic strings and pads
- identity consistency: tốt
- image: yes · video(8s): yes

### painterly-realism-cinematic — Điện ảnh sơn dầu / Cinematic painterly realism
- category: narrative-safe
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: The v0.2 default — cinematic 4K with painterly realism, muted
  desaturated palette, ink-wash background suggestion. Reproduces prior output.
- style descriptors: cinematic 4K painterly realism, restrained wuxia framing,
  muted desaturated palette, ink-wash depth, silk-and-mist choreography.
- Style block (EN, paste-ready): cinematic 4K painterly realism, restrained ancient
  Chinese fantasy framing, muted desaturated palette with selective jade-green and
  silver-grey accents, ink-wash background suggestion, soft film grain, original
  character faces, 16:9 aspect ratio.
- palette: muted desaturated base, jade-green + silver-grey accents
- style negatives: no neon saturation, no anime cel-shading, no flat cartoon outlines, no video-game CG sheen
- music/score anchor: restrained guzheng + erhu orchestral, cinematic and intimate
- identity consistency: tốt
- image: yes · video(8s): yes

### semi-realistic-digital-painting — Digital painting bán tả thực
- category: narrative-safe
- best-fit genres: đô thị, huyền huyễn, tiên hiệp
- description: Textured-brush digital illustration with semi-realistic anatomy and
  emotive lighting — the polished fantasy-illustration look.
- style descriptors: semi-realistic digital fantasy painting, textured brushwork,
  rim-lit hair and fabric, atmospheric particles, emotive faces.
- Style block (EN, paste-ready): semi-realistic digital fantasy painting, visible
  textured brush strokes, soft rim-lit hair and fabric, atmospheric depth with
  rain/wind/light particles, painterly skin, original character faces, 16:9 aspect ratio.
- palette: cool desaturated mid-tones, luminous backlight, selective warm accents
- style negatives: no 3D render sheen, no flat vector shapes, no photographic detail, no hard CGI edges
- music/score anchor: ambient cinematic — solo erhu or piano over sustained string pads, intimate and emotive
- identity consistency: tốt
- image: yes · video(8s): weak

### light-novel-moe — Light-novel anime / moe mềm
- category: narrative-safe
- best-fit genres: đô thị, tiên hiệp
- description: Soft anime light-novel aesthetic — clean lineart, gentle gradient
  shading, large expressive eyes, bright airy palette.
- style descriptors: soft anime light-novel illustration, clean lineart, gentle
  gradient cel shading, airy palette, expressive faces.
- Style block (EN, paste-ready): soft anime light-novel illustration with clean
  lineart, gentle gradient cel shading, expressive large eyes, bright airy color
  grading, subtle bloom, delicate detailing on hair and clothing, 16:9 aspect ratio.
- palette: pastel brights, soft pink/blue/cream, high-key lighting
- style negatives: no photographic realism, no muted gritty palette, no heavy painterly texture, no Western cartoon proportions
- music/score anchor: light orchestral + piano, gentle and warm; slice-of-life anime score register
- identity consistency: tốt
- image: yes · video(8s): weak

### concept-art-cityscape — Concept art toàn cảnh
- category: narrative-safe
- best-fit genres: huyền huyễn, đô thị, tiên hiệp
- description: Matte-painting environment concept art — sweeping vistas, epic
  architecture, atmospheric perspective; characters small in frame.
- style descriptors: cinematic environment concept art, matte painting, sweeping
  vistas, strong atmospheric perspective, detailed Chinese architecture.
- Style block (EN, paste-ready): cinematic environment concept art / matte painting,
  epic wide vista, strong atmospheric perspective and depth haze, dramatic god-rays,
  detailed Chinese architecture, painterly rendering with photo-real lighting,
  16:9 aspect ratio.
- palette: atmospheric blues/greys with warm focal accents, high dynamic range
- style negatives: no flat anime shading, no cartoon outlines, no tight close-up portrait framing, no chibi proportions
- music/score anchor: epic orchestral ambient — broad strings, low brass swells, ethereal pads conveying scale
- identity consistency: khá
- image: yes · video(8s): yes

### dark-fantasy-modao — Ma đạo hắc ám / Dark demonic-cultivation
- category: narrative-safe
- best-fit genres: huyền huyễn, tiên hiệp
- description: Brooding 2D-on-3D hybrid donghua — demonic cultivation, shadow and
  blood-red accents, ornate but grim.
- style descriptors: dark demonic-cultivation donghua, 2D cel characters over
  detailed 3D sets, low-key lighting, ornate robes, resentful-energy smoke.
- Style block (EN, paste-ready): dark-fantasy Chinese donghua look, 2D cel
  characters over detailed 3D sets, moody low-key lighting, ornate robes, drifting
  resentful-energy smoke, blood-red and ink-black accents, original character faces,
  16:9 aspect ratio.
- palette: ink-black, deep crimson, ash-grey, cold moonlight blue
- style negatives: no bright high-key lighting, no pastel palette, no photographic realism, no cheerful moe styling
- music/score anchor: dark ethnic orchestral — low guqin/erhu, ominous taiko, choir-as-pad (wordless), brooding
- identity consistency: tốt
- image: yes · video(8s): yes

### game-cg-25d — Game CG 2.5D
- category: narrative-safe
- best-fit genres: tiên hiệp, huyền huyễn, đô thị
- description: Polished cel-shaded 2.5D game CG — crisp toon shading on 3D
  models, vivid colors, gacha-art polish.
- style descriptors: polished cel-shaded 2.5D game CG, toon-shaded 3D characters,
  crisp outlines, vivid colors, glossy highlights, detailed costumes.
- Style block (EN, paste-ready): polished cel-shaded 2.5D game CG, toon-shaded 3D
  characters with crisp ink outlines, vivid saturated colors, glossy highlights,
  stylized proportions, clean detailed costumes, original character faces,
  16:9 aspect ratio.
- palette: vivid saturated primaries, bright skies, glowing element FX
- style negatives: no photographic realism, no muted desaturation, no rough painterly texture, no live-action film grain
- music/score anchor: adventurous orchestral game-score hybrid — Chinese instruments + full orchestra, bright and kinetic
- identity consistency: tốt
- image: yes · video(8s): yes

### dark-zhiguai-folk-horror — Chí quái dân gian / Folk horror
- category: narrative-safe
- best-fit genres: huyền huyễn, cổ điển
- description: Eerie classical folk-tale horror — yaoguai, painted-skin demons,
  ominous mood drawn from zhiguai strange-tale tradition.
- style descriptors: eerie Chinese folk-horror illustration, muted painterly
  palette, fog, candlelight, yaoguai/spirit imagery, ominous negative space.
- Style block (EN, paste-ready): eerie Chinese folk-horror illustration, painterly
  with unsettling muted palette, fog and candlelight, yaoguai/spirit imagery,
  ominous negative space, subtle grain, original character faces, 16:9 aspect ratio.
- palette: desaturated earth tones, sickly green, dim candle-amber, deep shadow
- style negatives: no cheerful bright palette, no cute moe styling, no clean game-CG sheen, no Western gothic horror tropes
- music/score anchor: dark ambient ritual drone — sparse guqin, breathy xiao, dissonant strings, unsettling
- identity consistency: khá
- image: yes · video(8s): yes

### scifi-donghua-kehuan — Khoa huyễn / Chinese sci-fi
- category: narrative-safe
- best-fit genres: đô thị, huyền huyễn
- description: Chinese sci-fi (kehuan) — hard-surface tech, neon megacity, used-future
  grit fused with Chinese design motifs.
- style descriptors: Chinese sci-fi kehuan render, hard-surface mecha and
  architecture, neon megacity haze, holographic UI, gritty used-future textures.
- Style block (EN, paste-ready): Chinese sci-fi kehuan cinematic render,
  hard-surface mecha and architecture, neon-lit megacity haze, holographic
  Chinese-character UI, gritty used-future textures, volumetric light, original
  character faces, 16:9 aspect ratio.
- palette: cyan/orange neon contrast, gunmetal greys, deep night-blue
- style negatives: no Tang-dynasty robes (unless flashback), no fantasy magic auras, no medieval setting, no pastel anime palette
- music/score anchor: synth-orchestral sci-fi — analog synth pads, deep sub-bass, cinematic strings, futuristic
- identity consistency: khá
- image: yes · video(8s): yes

### manhua — Manhua / Chinese webcomic
- category: narrative-safe
- best-fit genres: đô thị, tiên hiệp, võ hiệp
- description: Clean-line Chinese webcomic look — bold lineart, flat-to-soft cel
  color, dynamic paneling energy.
- style descriptors: Chinese manhua/webcomic illustration, bold clean lineart,
  flat-to-soft cel coloring, dynamic action posing, simple gradient backgrounds.
- Style block (EN, paste-ready): Chinese manhua / webcomic illustration, bold clean
  lineart, flat-to-soft cel coloring, dynamic action posing, simple gradient
  backgrounds, vibrant but controlled palette, 16:9 aspect ratio.
- palette: clean saturated mid-tones, crisp blacks, simple gradients
- style negatives: no photographic realism, no heavy oil-paint texture, no 3D render sheen, no muted film grain
- music/score anchor: light modern hybrid — orchestral with subtle electronic pulse, energetic
- identity consistency: tốt
- image: yes · video(8s): weak

### ink-wash-stylized — Thủy mặc cách điệu / Stylized ink-wash (still)
- category: accent-title-card
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: Stylized still shuimo brushwork — wet ink bleed, vast negative space,
  monochrome with sparse color. Striking but holds faces poorly across shots.
- style descriptors: traditional shuimo ink-wash brushwork, wet ink bleed,
  rice-paper texture, vast negative space, sparse color accents.
- Style block (EN, paste-ready): traditional Chinese ink-wash (shuimo) painting,
  expressive wet brush strokes with controlled ink bleed, vast negative space,
  monochrome black ink with one or two restrained color accents, rice-paper texture,
  16:9 aspect ratio.
- palette: black ink gradients on off-white paper, sparse vermilion or indigo accent
- style negatives: no photographic detail, no 3D render, no hard CGI edges, no saturated color, no anime cel-shading
- music/score anchor: minimalist guqin solo with long silences, meditative ink-wash register
- identity consistency: khó
- image: yes · video(8s): weak

### flat-poster-silhouette — Poster phẳng / Flat color-block silhouette
- category: accent-title-card
- best-fit genres: võ hiệp, cổ điển, huyền huyễn
- description: Bold flat color-block poster art with silhouettes and limited palette —
  great for title cards, weak for consistent close-ups.
- style descriptors: flat graphic poster art, bold color blocks, dramatic
  silhouettes, limited palette, high-contrast negative space.
- Style block (EN, paste-ready): flat graphic poster illustration, bold color-block
  shapes, dramatic silhouettes, limited 2-3 color palette, strong negative space,
  high-contrast composition, subtle paper grain, 16:9 aspect ratio.
- palette: 2-3 bold flats (e.g. crimson + black + cream), high contrast
- style negatives: no photographic detail, no gradient realism, no 3D render, no busy background clutter
- music/score anchor: bold minimal percussion + single sustained instrument, dramatic
- identity consistency: khó
- image: yes · video(8s): weak

### traditional-pattern-minimal — Hoa văn truyền thống tối giản
- category: accent-title-card
- best-fit genres: cổ điển, tiên hiệp
- description: Decorative traditional motifs (clouds, dragons, lattice) over generous
  negative space — elegant minimal title-card art.
- style descriptors: traditional Chinese decorative motifs, auspicious clouds,
  dragon scrollwork, lattice borders, gold-leaf accents.
- Style block (EN, paste-ready): minimalist decorative composition built from
  traditional Chinese motifs (auspicious clouds, dragon scrollwork, lattice borders),
  generous negative space, refined line ornament, restrained palette, gold-leaf
  accents, 16:9 aspect ratio.
- palette: cream/ink base with gold + one imperial accent (vermilion or jade)
- style negatives: no photographic realism, no 3D render, no cluttered detail, no Western ornament
- music/score anchor: refined court chamber — guqin/xiao with light chimes, elegant and sparse
- identity consistency: khó
- image: yes · video(8s): weak

### watercolor-gouache — Màu nước / Watercolor-gouache
- category: accent-title-card
- best-fit genres: cổ điển, đô thị, tiên hiệp
- description: Soft watercolor / gouache wash — bleeding edges, paper texture, gentle
  lyrical mood. Lovely but loses facial precision shot-to-shot.
- style descriptors: soft Chinese watercolor and gouache illustration, bleeding
  pigment edges, paper texture, gentle layered washes.
- Style block (EN, paste-ready): soft watercolor and gouache illustration, bleeding
  pigment edges, visible paper texture, gentle layered washes, lyrical diffused light,
  delicate detailing, 16:9 aspect ratio.
- palette: soft translucent washes, harmonious low-saturation hues
- style negatives: no hard CGI edges, no 3D render, no photographic detail, no heavy black outlines
- music/score anchor: gentle solo piano or pipa with soft strings, lyrical and warm
- identity consistency: khó
- image: yes · video(8s): weak

### minimalist-calligraphy-symbolic — Thư pháp tối giản tượng trưng
- category: accent-title-card
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: Calligraphy strokes + a single symbol over dominant negative space —
  conceptual title art, not for character scenes.
- style descriptors: expressive Chinese calligraphy strokes, red seal accents,
  symbolic object, dominant negative space.
- Style block (EN, paste-ready): minimalist composition centered on expressive
  Chinese calligraphy brush strokes and a single symbolic element (sword, moon, seal),
  dominant negative space, monochrome ink with one red seal accent, rice-paper
  texture, 16:9 aspect ratio.
- palette: black ink on off-white, single vermilion seal accent
- style negatives: no photographic detail, no 3D render, no busy scene, no realistic faces
- music/score anchor: single resonant instrument (guqin pluck, struck bell) with deep silence
- identity consistency: khó
- image: yes · video(8s): weak

### folk-nianhua — Tranh niên hoạ dân gian / New Year woodblock print
- category: accent-title-card
- best-fit genres: cổ điển, huyền huyễn
- description: Folk New Year woodblock-print art — bold outlines, flat festive colors,
  symmetrical auspicious composition. Distinctive but stylized faces.
- style descriptors: Chinese folk New Year woodblock-print nianhua, bold black
  outlines, flat festive colors, symmetrical auspicious composition.
- Style block (EN, paste-ready): Chinese folk New Year woodblock-print nianhua,
  bold black outlines, flat festive color fills, symmetrical auspicious composition,
  decorative borders, printed-paper texture, original character faces, 16:9 aspect ratio.
- palette: festive red, gold, green, indigo on cream
- style negatives: no photographic realism, no 3D render, no soft gradient shading, no Western illustration style
- music/score anchor: festive folk ensemble — suona, gongs, drums, lively and ceremonial
- identity consistency: khó
- image: yes · video(8s): weak

### photobash-epic-poster — Photobash poster sử thi
- category: accent-title-card
- best-fit genres: huyền huyễn, cổ điển, đô thị
- description: Photobashed cinematic key-art — composited photo textures + paintover,
  epic dramatic lighting. Great hero poster, inconsistent as a face identity guide.
- style descriptors: epic cinematic key-art, composited realistic textures,
  painterly overpaint, dramatic rim and volumetric lighting.
- Style block (EN, paste-ready): epic cinematic key-art via photobashing, composited
  realistic textures with painterly overpaint, dramatic rim and volumetric lighting,
  heroic low-angle composition, high detail and contrast, 16:9 aspect ratio.
- palette: cinematic teal-orange or desaturated epic grade, strong focal light
- style negatives: no flat cartoon shading, no anime outlines, no chibi proportions, no clean vector look
- music/score anchor: epic trailer orchestral — big percussion, brass swells, choir-as-pad, grand
- identity consistency: khá
- image: yes · video(8s): weak

### ink-wash-animation — Thuỷ mặc động / Ink-wash animation
- category: video-oriented
- best-fit genres: cổ điển, tiên hiệp, võ hiệp
- description: Moving traditional ink-wash animation — wet brush forms drifting and
  morphing in motion. Designed for video; still frames look unfinished.
- style descriptors: traditional Chinese ink-wash animation, soft brushed forms,
  wet-ink diffusion in motion, flowing morphing strokes, vast negative space.
- Style block (EN, paste-ready): traditional Chinese ink-wash animation, soft brushed
  forms with wet-ink diffusion in motion, monochrome ink on rice paper, flowing
  morphing strokes, vast negative space, original character faces, 16:9 aspect ratio.
- palette: black ink gradients on off-white, occasional pale wash
- style negatives: no hard CGI edges, no 3D render, no photographic detail, no saturated color, no sharp anime outlines
- music/score anchor: solo guqin/dizi with natural ambience (water, wind), serene and flowing
- identity consistency: khó
- image: weak · video(8s): yes
