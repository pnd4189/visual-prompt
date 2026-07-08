# Music Mood Mapping — Genre × Emotion → Lyria Instrumental Prompt

> Related: [[genre-keywords]] · [[youtube-pacing-guide]]

Knowledge table for building **instrumental** Lyria 3 prompts (Lyria app). Maps
each supported genre × mood bucket → instrument palette, tempo (BPM), suggested
key/scale, and English mood descriptors. Use these to fill the DeepMind Lyria
template:

`[Genre & style] + [Mood] + [Instrumentation] + [Tempo/BPM + key] + "Instrumental."`

All palettes are **instrument-only**. Never include vocals, choir-as-lyrics, or
spoken word. Wordless ambient pads are allowed; sung/lyric content is not.

**Supported genres:** tien-hiep, huyen-huyen, do-thi, co-dien, vo-hiep.
**Mood buckets:** calm/intro · mystery/journey · tension/battle · sad/reflection ·
triumph/resolution.

## Global Music Register

These prompts are for audiobook background music, not trailers or battle cuts.
Always keep the result gentle, emotional, deep, spacious, and instrumental. The
music should support narration without overpowering it.

- Preferred BPM range: 55-86 for all moods.
- `tension / battle` means restrained suspense underscore, not action music.
- Avoid: fast ostinato, pounding percussion, war drums, aggressive brass, explosive
  impacts, trailer crescendos, high-energy chase rhythm.
- Use: soft guzheng/pipa/dizi/erhu, warm strings, low drones, light frame drum,
  distant gong bloom, airy reverb, slow rise-and-release.

---

## 1. Tiên Hiệp (Xianxia — cultivation, immortal sects)

Base style (default): *traditional Chinese orchestral + ambient*; override the register with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | guzheng, dizi flute, soft erhu, ambient pads | 60-72 | D major pentatonic | serene, meditative, misty mountain dawn, floating |
| mystery / journey | pipa, bamboo flute, low drone, light percussion | 70-84 | A minor pentatonic | mysterious, wandering, ancient, unfolding |
| tension / battle | soft low strings, sparse guzheng, breathy dizi, distant frame drum | 66-82 | E minor pentatonic | restrained, solemn, quietly tense, emotional pressure |
| sad / reflection | solo erhu, sparse guzheng, sustained strings | 56-66 | B minor | melancholic, wistful, longing, loss |
| triumph / resolution | warm Chinese strings, dizi, gentle gong, soft guzheng | 72-86 | G major | uplifting, transcendent, tender resolution, vast |

---

## 2. Huyền Huyễn (Xuanhuan — mythic fantasy, mixed magic)

Base style (default): *epic hybrid orchestral + ethnic Chinese, grand mythic register*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | hulusi, soft strings, harp, airy pads | 64-76 | C major | dreamlike, mythic calm, otherworldly |
| mystery / journey | pipa, ambient synth pad, low soft pulse, dizi | 70-84 | D minor | enigmatic, primordial, quiet quest |
| tension / battle | low strings, soft frame drum, airy drones, distant gong bloom | 66-82 | F minor | restrained mythic pressure, solemn, shadowed, controlled |
| sad / reflection | erhu, cello, soft piano, sustained pad | 54-64 | A minor | sorrowful, fated, ancient grief |
| triumph / resolution | warm orchestra, wordless airy pad, gentle gong, lyrical strings | 72-86 | E major | divine, relieved, luminous, legendary but soft |

---

## 3. Đô Thị (Urban — modern setting with hidden cultivation)

Base style (default): *modern cinematic, subtle electronic*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | electric piano, warm pads, soft nylon guitar, light vinyl texture | 70-84 | F major | mellow, neon-lit night, intimate, contemporary |
| mystery / journey | muted synth pad, atmospheric drone, sparse piano, light texture | 72-86 | G minor | cool, urban intrigue, understated tension |
| tension / battle | low soft synth, cello pulses, rain ambience, sparse percussion | 66-82 | A minor | restrained, high-stakes but quiet, watchful |
| sad / reflection | solo piano, cello, rain ambience, soft pad | 58-70 | D minor | lonely, rainy city, bittersweet |
| triumph / resolution | warm synth pad, bright piano, gentle strings | 72-86 | C major | empowered, cathartic, calm after struggle |

---

## 4. Cổ Điển (Gu Dian — historical court, no magic)

Base style (default): *period Chinese orchestral, courtly opulence*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | guqin, xiao flute, soft strings, light chimes | 56-68 | D major pentatonic | refined, courtly, tranquil palace dawn |
| mystery / journey | pipa, dizi, low strings, light ceremonial percussion | 68-82 | E minor pentatonic | stately, political intrigue, measured |
| tension / battle | guqin low notes, soft strings, distant frame drum, muted sheng | 64-80 | C minor | restrained court danger, solemn, dramatic but quiet |
| sad / reflection | guqin solo, erhu, sparse strings | 52-62 | A minor | mournful, dynastic sorrow, elegy |
| triumph / resolution | soft period orchestra, ceremonial gong bloom, lyrical dizi | 70-84 | G major | majestic, ceremonial, warm resolution |

---

## 5. Võ Hiệp (Wuxia — jianghu martial chivalry, no cultivation)

Base style (default): *lean ethnic Chinese + percussion, martial choreography energy*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | dizi, guzheng, soft erhu, ambient wind | 62-74 | D major pentatonic | tranquil, bamboo grove, drifting |
| mystery / journey | pipa, low soft pulse, bamboo flute, light strings | 70-84 | A minor pentatonic | wandering jianghu, watchful, road-worn |
| tension / battle | soft frame drum, low strings, restrained erhu, muted pipa | 66-82 | E minor | quiet duel memory, restrained sword tension, emotional |
| sad / reflection | solo erhu, sparse guzheng, sustained pad | 54-64 | B minor | honor lost, lonely swordsman, rueful |
| triumph / resolution | ensemble strings, dizi, gentle gong, light percussion | 72-86 | G major | heroic but gentle, chivalrous resolve, sweeping softly |

---

## Negative line (always append, instrumental enforcement)

```
no vocals, no lyrics, no singing, no spoken word, no rap, no choir words
```

## Loop cue (always append)

```
seamless loop, no fade out, ~2-3 minutes
```

## Notes

- Lyria responds best to **English**. Keep the prompt body English; only the
  navigation label is Vietnamese.
- Wordless airy pad texture is acceptable for huyền huyễn grandeur — it is a
  timbre, not lyrics. Still keep the negative line to suppress sung words.
- If `--music N` requests more regions than there are distinct moods, repeat the
  arc with varied intensity/instrumentation so each loop stays distinct.
