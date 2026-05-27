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
| `semi-realistic-digital-painting` | narrative-safe | ArtStation textured-brush digital painting |
| `light-novel-moe` | narrative-safe | soft anime light-novel aesthetic, clean moe shading |
| `concept-art-cityscape` | narrative-safe | matte-painting environment / vista concept art |
| `dark-fantasy-modao` | narrative-safe | brooding 2D/3D-hybrid demonic-cultivation donghua |
| `game-cg-25d` | narrative-safe | miHoYo-style cel-shaded 2.5D game CG |
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
| `ink-wash-animation` | video-oriented | moving Te Wei-style ink-wash animation |

---

## Entries

### donghua-xianxia — Tiên hiệp Donghua / Chinese 3D cultivation donghua
- category: narrative-safe
- best-fit genres: tiên hiệp, huyền huyễn
- description: Glossy 3D-rendered cultivation world with cel-lit characters,
  flowing robes, floating sect architecture and qi effects — the modern donghua look.
- reference anchors: *A Record of a Mortal's Journey to Immortality* (凡人修仙传,
  2020, Original Force / Wonder Cat Animation, Bilibili); *The Daily Life of the
  Immortal King*.
- Style block (EN, paste-ready): high-end Chinese 3D donghua render in the style of
  *A Record of a Mortal's Journey to Immortality*, cel-shaded characters with soft
  subsurface skin, physically-based cloth on flowing silk robes, volumetric qi mist,
  saturated cinematic key light, clean rim lighting, 16:9 aspect ratio.
- palette: jade-green, cyan qi glow, warm gold highlights, deep indigo shadow
- style negatives: no live-action photographic skin, no muted live-action desaturation, no Western 3D cartoon proportions, no claymation
- music/score anchor: synth-orchestral donghua hybrid — Chinese ethnic instruments (guzheng, dizi) over modern cinematic strings and pads
- anchor consistency: tốt
- image: yes · video(8s): yes

### painterly-realism-cinematic — Điện ảnh sơn dầu / Cinematic painterly realism
- category: narrative-safe
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: The v0.2 default — cinematic 4K with painterly realism, muted
  desaturated palette, ink-wash background suggestion. Reproduces prior output.
- reference anchors: *Crouching Tiger, Hidden Dragon* (2000, dir. Ang Lee);
  *Hero* (2002, dir. Zhang Yimou).
- Style block (EN, paste-ready): cinematic 4K, painterly realism in the visual
  language of *Crouching Tiger, Hidden Dragon* (2000), muted desaturated palette with
  selective jade-green and silver-grey accents, ink-wash background suggestion,
  soft film grain, 16:9 aspect ratio.
- palette: muted desaturated base, jade-green + silver-grey accents
- style negatives: no neon saturation, no anime cel-shading, no flat cartoon outlines, no video-game CG sheen
- music/score anchor: Tan Dun-style guzheng + erhu orchestral, cinematic and restrained (Crouching Tiger register)
- anchor consistency: tốt
- image: yes · video(8s): yes

### semi-realistic-digital-painting — Digital painting bán tả thực
- category: narrative-safe
- best-fit genres: đô thị, huyền huyễn, tiên hiệp
- description: Textured-brush digital illustration with semi-realistic anatomy and
  emotive lighting — the ArtStation fantasy-illustration look.
- reference anchors: WLOP (Wang Ling, *Ghostblade*); ArtStation Chinese
  fantasy-illustration community.
- Style block (EN, paste-ready): semi-realistic digital painting in the style of WLOP
  / *Ghostblade*, visible textured brush strokes, soft rim-lit hair and fabric,
  atmospheric depth with rain/wind/light particles, painterly skin, 16:9 aspect ratio.
- palette: cool desaturated mid-tones, luminous backlight, selective warm accents
- style negatives: no 3D render sheen, no flat vector shapes, no photographic detail, no hard CGI edges
- music/score anchor: ambient cinematic — solo erhu or piano over sustained string pads, intimate and emotive
- anchor consistency: tốt
- image: yes · video(8s): weak

### light-novel-moe — Light-novel anime / moe mềm
- category: narrative-safe
- best-fit genres: đô thị, tiên hiệp
- description: Soft anime light-novel aesthetic — clean lineart, gentle gradient
  shading, large expressive eyes, bright airy palette.
- reference anchors: Kyoto Animation soft-shading aesthetic; Japanese light-novel
  adaptation illustration; Chinese moe webtoon covers.
- Style block (EN, paste-ready): soft anime light-novel illustration with clean
  lineart, gentle gradient cel shading, expressive large eyes, bright airy color
  grading, subtle bloom, delicate detailing on hair and clothing, 16:9 aspect ratio.
- palette: pastel brights, soft pink/blue/cream, high-key lighting
- style negatives: no photographic realism, no muted gritty palette, no heavy painterly texture, no Western cartoon proportions
- music/score anchor: light orchestral + piano, gentle and warm; slice-of-life anime score register
- anchor consistency: tốt
- image: yes · video(8s): weak

### concept-art-cityscape — Concept art toàn cảnh
- category: narrative-safe
- best-fit genres: huyền huyễn, đô thị, tiên hiệp
- description: Matte-painting environment concept art — sweeping vistas, epic
  architecture, atmospheric perspective; characters small in frame.
- reference anchors: Feng Zhu (FZD); *Black Myth: Wukong* (2024, Game Science)
  environment art; ArtStation matte-painting community.
- Style block (EN, paste-ready): cinematic environment concept art / matte painting,
  epic wide vista, strong atmospheric perspective and depth haze, dramatic god-rays,
  detailed Chinese architecture, painterly rendering with photo-real lighting,
  16:9 aspect ratio.
- palette: atmospheric blues/greys with warm focal accents, high dynamic range
- style negatives: no flat anime shading, no cartoon outlines, no tight close-up portrait framing, no chibi proportions
- music/score anchor: epic orchestral ambient — broad strings, low brass swells, ethereal pads conveying scale
- anchor consistency: khá
- image: yes · video(8s): yes

### dark-fantasy-modao — Ma đạo hắc ám / Dark demonic-cultivation
- category: narrative-safe
- best-fit genres: huyền huyễn, tiên hiệp
- description: Brooding 2D-on-3D hybrid donghua — demonic cultivation, shadow and
  blood-red accents, ornate but grim.
- reference anchors: *Mo Dao Zu Shi* (魔道祖师 / The Founder of Diabolism, 2018,
  B.CMAY Pictures, Tencent).
- Style block (EN, paste-ready): dark-fantasy Chinese donghua in the style of *Mo Dao
  Zu Shi*, 2D cel characters over detailed 3D sets, moody low-key lighting, ornate
  robes, drifting resentful-energy smoke, blood-red and ink-black accents,
  16:9 aspect ratio.
- palette: ink-black, deep crimson, ash-grey, cold moonlight blue
- style negatives: no bright high-key lighting, no pastel palette, no photographic realism, no cheerful moe styling
- music/score anchor: dark ethnic orchestral — low guqin/erhu, ominous taiko, choir-as-pad (wordless), brooding
- anchor consistency: tốt
- image: yes · video(8s): yes

### game-cg-25d — Game CG 2.5D
- category: narrative-safe
- best-fit genres: tiên hiệp, huyền huyễn, đô thị
- description: miHoYo-style cel-shaded 2.5D game CG — crisp toon shading on 3D
  models, vivid colors, gacha-art polish.
- reference anchors: *Genshin Impact*, *Honkai: Star Rail* (HoYoverse / miHoYo,
  cel-shaded).
- Style block (EN, paste-ready): cel-shaded 2.5D game CG in the style of *Genshin
  Impact*, toon-shaded 3D characters with crisp ink outlines, vivid saturated colors,
  glossy highlights, anime proportions, clean detailed costumes, 16:9 aspect ratio.
- palette: vivid saturated primaries, bright skies, glowing element FX
- style negatives: no photographic realism, no muted desaturation, no rough painterly texture, no live-action film grain
- music/score anchor: orchestral game-score hybrid — Chinese instruments + full orchestra, adventurous and bright (HoYo-mix register)
- anchor consistency: tốt
- image: yes · video(8s): yes

### dark-zhiguai-folk-horror — Chí quái dân gian / Folk horror
- category: narrative-safe
- best-fit genres: huyền huyễn, cổ điển
- description: Eerie classical folk-tale horror — yaoguai, painted-skin demons,
  ominous mood drawn from zhiguai strange-tale tradition.
- reference anchors: *Yao-Chinese Folktales* (中国奇谭, 2023, Shanghai Animation
  Film Studio); *Painted Skin* (画皮, 2008); *Strange Tales from a Chinese Studio*
  (Liaozhai) imagery.
- Style block (EN, paste-ready): eerie Chinese folk-horror illustration in the spirit
  of *Yao-Chinese Folktales*, painterly with unsettling muted palette, fog and
  candlelight, yaoguai/spirit imagery, ominous negative space, subtle grain,
  16:9 aspect ratio.
- palette: desaturated earth tones, sickly green, dim candle-amber, deep shadow
- style negatives: no cheerful bright palette, no cute moe styling, no clean game-CG sheen, no Western gothic horror tropes
- music/score anchor: dark ambient ritual drone — sparse guqin, breathy xiao, dissonant strings, unsettling
- anchor consistency: khá
- image: yes · video(8s): yes

### scifi-donghua-kehuan — Khoa huyễn / Chinese sci-fi
- category: narrative-safe
- best-fit genres: đô thị, huyền huyễn
- description: Chinese sci-fi (kehuan) — hard-surface tech, neon megacity, used-future
  grit fused with Chinese design motifs.
- reference anchors: *The Wandering Earth* (流浪地球, 2019/2023, dir. Frant Gwo);
  Chinese sci-fi donghua.
- Style block (EN, paste-ready): Chinese sci-fi (kehuan) cinematic render in the
  spirit of *The Wandering Earth*, hard-surface mecha and architecture, neon-lit
  megacity haze, holographic Chinese-character UI, gritty used-future textures,
  volumetric light, 16:9 aspect ratio.
- palette: cyan/orange neon contrast, gunmetal greys, deep night-blue
- style negatives: no Tang-dynasty robes (unless flashback), no fantasy magic auras, no medieval setting, no pastel anime palette
- music/score anchor: synth-orchestral sci-fi — analog synth pads, deep sub-bass, cinematic strings, futuristic
- anchor consistency: khá
- image: yes · video(8s): yes

### manhua — Manhua / Chinese webcomic
- category: narrative-safe
- best-fit genres: đô thị, tiên hiệp, võ hiệp
- description: Clean-line Chinese webcomic look — bold lineart, flat-to-soft cel
  color, dynamic paneling energy.
- reference anchors: Chinese webtoon/manhua adaptations (*Tales of Demons and Gods*,
  *Battle Through the Heavens* manhua); Kuaikan/Bilibili Comics house style.
- Style block (EN, paste-ready): Chinese manhua / webcomic illustration, bold clean
  lineart, flat-to-soft cel coloring, dynamic action posing, simple gradient
  backgrounds, vibrant but controlled palette, 16:9 aspect ratio.
- palette: clean saturated mid-tones, crisp blacks, simple gradients
- style negatives: no photographic realism, no heavy oil-paint texture, no 3D render sheen, no muted film grain
- music/score anchor: light modern hybrid — orchestral with subtle electronic pulse, energetic
- anchor consistency: tốt
- image: yes · video(8s): weak

### ink-wash-stylized — Thủy mặc cách điệu / Stylized ink-wash (still)
- category: accent-title-card
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: Stylized still shuimo brushwork — wet ink bleed, vast negative space,
  monochrome with sparse color. Striking but holds faces poorly across shots.
- reference anchors: Qi Baishi; Wu Guanzhong; *Black Myth: Wukong* (2024) ink-wash
  ending cutscenes.
- Style block (EN, paste-ready): traditional Chinese ink-wash (shuimo) painting,
  expressive wet brush strokes with controlled ink bleed, vast negative space,
  monochrome black ink with one or two restrained color accents, rice-paper texture,
  16:9 aspect ratio.
- palette: black ink gradients on off-white paper, sparse vermilion or indigo accent
- style negatives: no photographic detail, no 3D render, no hard CGI edges, no saturated color, no anime cel-shading
- music/score anchor: minimalist guqin solo with long silences, meditative ink-wash register
- anchor consistency: khó
- image: yes · video(8s): weak

### flat-poster-silhouette — Poster phẳng / Flat color-block silhouette
- category: accent-title-card
- best-fit genres: võ hiệp, cổ điển, huyền huyễn
- description: Bold flat color-block poster art with silhouettes and limited palette —
  great for title cards, weak for consistent close-ups.
- reference anchors: *Hero* (2002) color-blocked sequences; modern minimalist film
  key-art / festival poster design.
- Style block (EN, paste-ready): flat graphic poster illustration, bold color-block
  shapes, dramatic silhouettes, limited 2-3 color palette, strong negative space,
  high-contrast composition, subtle paper grain, 16:9 aspect ratio.
- palette: 2-3 bold flats (e.g. crimson + black + cream), high contrast
- style negatives: no photographic detail, no gradient realism, no 3D render, no busy background clutter
- music/score anchor: bold minimal percussion + single sustained instrument, dramatic
- anchor consistency: khó
- image: yes · video(8s): weak

### traditional-pattern-minimal — Hoa văn truyền thống tối giản
- category: accent-title-card
- best-fit genres: cổ điển, tiên hiệp
- description: Decorative traditional motifs (clouds, dragons, lattice) over generous
  negative space — elegant minimal title-card art.
- reference anchors: Dunhuang mural motifs; Forbidden City decorative patterns;
  Chinese cloud/dragon ornament (yunwen).
- Style block (EN, paste-ready): minimalist decorative composition built from
  traditional Chinese motifs (auspicious clouds, dragon scrollwork, lattice borders),
  generous negative space, refined line ornament, restrained palette, gold-leaf
  accents, 16:9 aspect ratio.
- palette: cream/ink base with gold + one imperial accent (vermilion or jade)
- style negatives: no photographic realism, no 3D render, no cluttered detail, no Western ornament
- music/score anchor: refined court chamber — guqin/xiao with light chimes, elegant and sparse
- anchor consistency: khó
- image: yes · video(8s): weak

### watercolor-gouache — Màu nước / Watercolor-gouache
- category: accent-title-card
- best-fit genres: cổ điển, đô thị, tiên hiệp
- description: Soft watercolor / gouache wash — bleeding edges, paper texture, gentle
  lyrical mood. Lovely but loses facial precision shot-to-shot.
- reference anchors: Chinese watercolor illustration; *Big Fish & Begonia*
  (大鱼海棠, 2016) lush painterly palette.
- Style block (EN, paste-ready): soft watercolor and gouache illustration, bleeding
  pigment edges, visible paper texture, gentle layered washes, lyrical diffused light,
  delicate detailing, 16:9 aspect ratio.
- palette: soft translucent washes, harmonious low-saturation hues
- style negatives: no hard CGI edges, no 3D render, no photographic detail, no heavy black outlines
- music/score anchor: gentle solo piano or pipa with soft strings, lyrical and warm
- anchor consistency: khó
- image: yes · video(8s): weak

### minimalist-calligraphy-symbolic — Thư pháp tối giản tượng trưng
- category: accent-title-card
- best-fit genres: cổ điển, võ hiệp, tiên hiệp
- description: Calligraphy strokes + a single symbol over dominant negative space —
  conceptual title art, not for character scenes.
- reference anchors: Wang Xizhi cursive calligraphy; Chinese seal (zhuanke) and ink
  seal aesthetics.
- Style block (EN, paste-ready): minimalist composition centered on expressive
  Chinese calligraphy brush strokes and a single symbolic element (sword, moon, seal),
  dominant negative space, monochrome ink with one red seal accent, rice-paper
  texture, 16:9 aspect ratio.
- palette: black ink on off-white, single vermilion seal accent
- style negatives: no photographic detail, no 3D render, no busy scene, no realistic faces
- music/score anchor: single resonant instrument (guqin pluck, struck bell) with deep silence
- anchor consistency: khó
- image: yes · video(8s): weak

### folk-nianhua — Tranh niên hoạ dân gian / New Year woodblock print
- category: accent-title-card
- best-fit genres: cổ điển, huyền huyễn
- description: Folk New Year woodblock-print art — bold outlines, flat festive colors,
  symmetrical auspicious composition. Distinctive but stylized faces.
- reference anchors: Yangliuqing (杨柳青) New Year prints; Taohuawu (桃花坞)
  woodblock nianhua.
- Style block (EN, paste-ready): Chinese folk New Year woodblock-print (nianhua) in
  the Yangliuqing tradition, bold black outlines, flat festive color fills,
  symmetrical auspicious composition, decorative borders, printed-paper texture,
  16:9 aspect ratio.
- palette: festive red, gold, green, indigo on cream
- style negatives: no photographic realism, no 3D render, no soft gradient shading, no Western illustration style
- music/score anchor: festive folk ensemble — suona, gongs, drums, lively and ceremonial
- anchor consistency: khó
- image: yes · video(8s): weak

### photobash-epic-poster — Photobash poster sử thi
- category: accent-title-card
- best-fit genres: huyền huyễn, cổ điển, đô thị
- description: Photobashed cinematic key-art — composited photo textures + paintover,
  epic dramatic lighting. Great hero poster, inconsistent as a face anchor.
- reference anchors: film key-art photobashing; ArtStation epic-poster / key-art
  community.
- Style block (EN, paste-ready): epic cinematic key-art via photobashing, composited
  realistic textures with painterly overpaint, dramatic rim and volumetric lighting,
  heroic low-angle composition, high detail and contrast, 16:9 aspect ratio.
- palette: cinematic teal-orange or desaturated epic grade, strong focal light
- style negatives: no flat cartoon shading, no anime outlines, no chibi proportions, no clean vector look
- music/score anchor: epic trailer orchestral — big percussion, brass swells, choir-as-pad, grand
- anchor consistency: khá
- image: yes · video(8s): weak

### ink-wash-animation — Thuỷ mặc động / Ink-wash animation
- category: video-oriented
- best-fit genres: cổ điển, tiên hiệp, võ hiệp
- description: Moving traditional ink-wash animation — wet brush forms drifting and
  morphing in motion. Designed for video; still frames look unfinished.
- reference anchors: Te Wei — *Feeling from Mountain and Water* (山水情, 1988) and
  *Little Tadpoles Looking for Mama* (小蝌蚪找妈妈, 1960), Shanghai Animation Film
  Studio.
- Style block (EN, paste-ready): traditional Chinese ink-wash animation in the style
  of Te Wei's *Feeling from Mountain and Water*, soft brushed forms with wet-ink
  diffusion in motion, monochrome ink on rice paper, flowing morphing strokes, vast
  negative space, 16:9 aspect ratio.
- palette: black ink gradients on off-white, occasional pale wash
- style negatives: no hard CGI edges, no 3D render, no photographic detail, no saturated color, no sharp anime outlines
- music/score anchor: solo guqin/dizi with natural ambience (water, wind), serene and flowing
- anchor consistency: khó
- image: weak · video(8s): yes
