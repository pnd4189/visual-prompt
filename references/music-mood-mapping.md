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

---

## 1. Tiên Hiệp (Xianxia — cultivation, immortal sects)

Base style (default): *traditional Chinese orchestral + ambient*; override the register with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | guzheng, dizi flute, soft erhu, ambient pads | 60-72 | D major pentatonic | serene, meditative, misty mountain dawn, floating |
| mystery / journey | pipa, bamboo flute, low drone, light percussion | 80-96 | A minor pentatonic | mysterious, wandering, ancient, unfolding |
| tension / battle | taiko drums, low strings, fast guzheng tremolo, erhu stabs | 120-140 | E minor (Phrygian color) | urgent, fierce, surging qi, climactic |
| sad / reflection | solo erhu, sparse guzheng, sustained strings | 56-66 | B minor | melancholic, wistful, longing, loss |
| triumph / resolution | full Chinese orchestra, swelling strings, dizi soaring, gentle gong | 90-110 | G major | uplifting, transcendent, ascension, vast |

---

## 2. Huyền Huyễn (Xuanhuan — mythic fantasy, mixed magic)

Base style (default): *epic hybrid orchestral + ethnic Chinese, grand mythic register*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | hulusi, soft strings, harp, airy pads | 64-76 | C major | dreamlike, mythic calm, otherworldly |
| mystery / journey | pipa, ambient synth pad, low taiko pulse, dizi | 84-100 | D minor | enigmatic, primordial, epic quest |
| tension / battle | massive taiko, brass swells, low strings ostinato, percussion | 128-150 | F minor | thunderous, godlike conflict, cataclysmic |
| sad / reflection | erhu, cello, soft piano, sustained pad | 54-64 | A minor | sorrowful, fated, ancient grief |
| triumph / resolution | epic orchestra, choir-as-pad (wordless), gong, soaring strings | 92-112 | E major | divine, victorious, soaring, legendary |

---

## 3. Đô Thị (Urban — modern setting with hidden cultivation)

Base style (default): *modern cinematic, subtle electronic*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | electric piano, warm pads, soft nylon guitar, light vinyl texture | 70-84 | F major | mellow, neon-lit night, intimate, contemporary |
| mystery / journey | muted synth bass, atmospheric pad, sparse piano, light hats | 90-104 | G minor | cool, urban intrigue, understated tension |
| tension / battle | driving synth bass, distorted strings, electronic percussion | 124-140 | A minor | pulsing, confrontational, high-stakes |
| sad / reflection | solo piano, cello, rain ambience, soft pad | 58-70 | D minor | lonely, rainy city, bittersweet |
| triumph / resolution | uplifting synth, live drums, bright piano, string section | 100-120 | C major | empowered, modern victory, cathartic |

---

## 4. Cổ Điển (Gu Dian — historical court, no magic)

Base style (default): *period Chinese orchestral, courtly opulence*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | guqin, xiao flute, soft strings, light chimes | 56-68 | D major pentatonic | refined, courtly, tranquil palace dawn |
| mystery / journey | pipa, dizi, low strings, ceremonial percussion | 78-92 | E minor pentatonic | stately, political intrigue, measured |
| tension / battle | war drums, brass-like sheng, fast strings, cymbals | 116-138 | C minor | martial, imperial conflict, dramatic |
| sad / reflection | guqin solo, erhu, sparse strings | 52-62 | A minor | mournful, dynastic sorrow, elegy |
| triumph / resolution | full period orchestra, ceremonial gong, soaring dizi | 88-108 | G major | majestic, imperial glory, ceremonial |

---

## 5. Võ Hiệp (Wuxia — jianghu martial chivalry, no cultivation)

Base style (default): *lean ethnic Chinese + percussion, martial choreography energy*; override with the chosen style's `music/score anchor` (see [[style-catalog]]).

| Mood | Instrumentation | BPM | Key / Scale | English descriptors |
|---|---|---|---|---|
| calm / intro | dizi, guzheng, soft erhu, ambient wind | 62-74 | D major pentatonic | tranquil, bamboo grove, drifting |
| mystery / journey | pipa, low percussion, bamboo flute, light strings | 84-98 | A minor pentatonic | wandering jianghu, watchful, road-worn |
| tension / battle | taiko, sharp percussion, fast erhu, low strings | 124-144 | E minor | duel, swift swordplay, kinetic |
| sad / reflection | solo erhu, sparse guzheng, sustained pad | 54-64 | B minor | honor lost, lonely swordsman, rueful |
| triumph / resolution | ensemble strings, dizi, gong, rising percussion | 90-110 | G major | heroic, chivalrous resolve, sweeping |

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
- Wordless "choir-as-pad" texture is acceptable for huyền huyễn grandeur — it is
  a timbre, not lyrics. Still keep the negative line to suppress sung words.
- If `--music N` requests more regions than there are distinct moods, repeat the
  arc with varied intensity/instrumentation so each loop stays distinct.
