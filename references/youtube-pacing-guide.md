# YouTube Pacing Guide — Image + Video Count Rationale

> Related: [[visual-prompt-template]] · [[scene-tag-camera-mapping]]

How many image prompts and video prompts to generate for a given audio
length. Source: YouTube algorithm penalizes static frames longer than ~8s
in audio-narration videos — viewers scroll away, retention drops, the
algorithm de-promotes.

## Formula

```
images = clamp(round(wordcount / 120), 120, 150)
videos = max(20, round(images / 6))
```

Explicit `--images` / `--videos` overrides are honored exactly. The default is a
production-heavy prompt pack; use overrides for quick tests.

## Pacing Tables

### 1-hour audio (~9,000 Vietnamese words narration)

| Item | Count | Cadence |
|---|---|---|
| Images | ~120 | one prompt per ~30s narration slot |
| Videos | ~20 | one motion prompt every ~3 min |

### 2-hour audio (~18,000 Vietnamese words narration)

| Item | Count | Cadence |
|---|---|---|
| Images | ~150 | one prompt per ~45–50s narration slot |
| Videos | ~25 | one motion prompt every ~5 min |

## Why 20+ video prompts?

- The final editor can choose fewer clips, but prompt generation should provide
  enough strong motion candidates.
- At least 20 clips gives coverage for openers, reveals, combat, ritual,
  breakthrough, travel, crowd, and climax moments.
- Image prompts carry the visual base; video prompts should be reserved for
  scenes where motion matters.

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

- 9,000 words / 120 images = 75 words per image prompt slot
- Average narration speed: 150 words/min Vietnamese
- 75 words ≈ 30 seconds per image prompt slot
- Each image displays 5–8s, then crossfade/cut to next OR a video clip plays
  in that slot (8s motion, then back to images)

YouTube algorithmic sweet spot: visual cut every 6–8s during editing. A
120-image + 20-video prompt pack gives enough source material for that edit
without forcing the editor to use every generated asset.
