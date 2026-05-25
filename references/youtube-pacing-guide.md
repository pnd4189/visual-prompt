# YouTube Pacing Guide — Image + Video Count Rationale

> Related: [[visual-prompt-template]] · [[scene-tag-camera-mapping]]

How many image prompts and video prompts to generate for a given audio
length. Source: YouTube algorithm penalizes static frames longer than ~8s
in audio-narration videos — viewers scroll away, retention drops, the
algorithm de-promotes.

## Formula

```
images = round(wordcount / 200)     # ≈ 1 image per ~200 words ≈ every 30–40s
videos = round(images   / 7)        # ≈ 1 short video per ~7 images
```

**Floor clamps:** `images >= 5`, `videos >= 2` (even very short clips need
visual variety).

## Pacing Tables

### 1-hour audio (~9,000 Vietnamese words narration)

| Item | Count | Cadence |
|---|---|---|
| Images | ~45 | one new image every ~80s (with 5–8s cuts) |
| Videos | ~6 | one video clip every ~10 min (8s each → 48s total motion) |

### 2-hour audio (~18,000 Vietnamese words narration)

| Item | Count | Cadence |
|---|---|---|
| Images | ~90 | one new image every ~80s |
| Videos | ~13 | one video clip every ~9 min |

## Why 1 video per ~7 images?

- Videos cost ~10× more compute than images (Veo3 limits, generation time).
- 1 video per ~10 minutes of audio is enough to refresh viewer attention.
- Image variety alone (45–90 distinct images per hour) carries the visual
  load. Videos are accents: openers, climax, transformation moments.

## Scene Placement Rhythm (which scenes get videos)

Flag scenes for video when:
- **Opening** — first scene of file (hooks viewer)
- **Climax** — pivotal action, battle, breakthrough, revelation
- **Action-dense** — duel, escape, transformation
- **Ritual reveal** — cultivation breakthrough, pill formation, weapon awakening
- **Travel transitions** — montage of journey (1 video instead of 5 static images)

**Do NOT flag for video:**
- Pure dialogue scenes (no motion to capture)
- Static meditation/contemplation (image is enough)
- Inner monologue (no visual motion)

## Cadence Math (1h audio example)

- 9,000 words / 45 images = 200 words per image
- Average narration speed: 150 words/min Vietnamese
- 200 words ≈ 80 seconds per image slot
- Each image displays 5–8s, then crossfade/cut to next OR a video clip plays
  in that slot (8s motion, then back to images)

YouTube algorithmic sweet spot: visual cut every 6–8s. A 45-image + 6-video
plan over 60min gives **~57 visual events** = avg 63s per slot. Stay below
80s/slot to keep retention high.
