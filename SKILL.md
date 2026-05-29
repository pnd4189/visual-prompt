---
name: visual-prompt
version: 0.5.0
description: Generate deep, copyright-safe, styleable image + video prompts (18-style catalog, recommend + select per run), a QA'd TTS-ready text, and Lyria music prompts from Vietnamese xianxia/wuxia novel files for YouTube audio videos in Antigravity/Agy CLI
license: MIT
contextFileName: SKILL.md
---

# Visual Prompt Skill

Antigravity/Agy CLI LLM-driven workflow that reads a Vietnamese xianxia/wuxia novel file
(.txt / .md / .docx, 2k–18k words, suitable for a 1–2h audio video). The skill
self-QAs the text first (no pre-proofread required), then emits four
paste-ready files:

- `<input>_qa.txt` — proofread, TTS-ready source of truth (residual Chinese/
  English removed, grammar fixed, long sentences split). Feed straight into
  TTS_Local (VieNeu / VietVoice).
- `<input>_image_prompts.txt` — deep 350–550 word sectioned image prompts
  (Camera / Story DNA / Setting / Composition / Subject / Action-Energy /
  Style / Lighting-Color / Atmosphere / Negative).
- `<input>_video_prompts.txt` — deep Veo3 5-part formula video prompts
  (Cinematography → Subject → Action `[00:00–00:02.5]` → Context →
  Style & Ambiance, audio embedded as scene layer).
- `<input>_music_prompts.txt` — instrumental Lyria 3 music prompts, one per
  mood region of the story arc (default 4, `--music N` override).

## Philosophy

- **Agy model is the loop driver.** The active Antigravity/Agy model reads input,
  plans scenes, writes prompts, and runs self-checks. Python only handles I/O the
  model can't do safely.
- **Deep prompt quality is mandatory.** Image/video/music prompts must include
  layered story DNA, character/prop locks, map-scale environment, foreground/
  midground/background composition, lighting/palette, action/energy/audio, and
  negative/safety rules. Shallow prompts are invalid.
- **Content-aware diversity.** Scene-mix targets follow the story's measured action
  density (combat-vocab scan): talky stories get a low action band and draw variety
  from camera/scale/group/insert/flashback — never from fabricated combat. Combat
  vocab stays available for stories that genuinely have it. `--epic` amplifies real
  scale on demand without inventing battles.
- **Original outputs only.** Do not copy web images, famous faces, celebrity
  likenesses, known-character faces, or exact IP/artist styles.
- **QA-first.** A proofread gate runs before everything else and produces the
  single QA'd source of truth that all downstream steps (bible, genre, scenes,
  music) consume. The skill no longer assumes pre-proofread input.
- **Reuses proven I/O scripts** from `chinese-novel-proofreader` v3.6.
- **Character bible verbatim.** Identity Anchor is pasted byte-for-byte into
  every scene so the same character looks the same across all images.
- **Cross-file series support** via `--series <name>` flag — bible persists in
  `~/.gemini/bibles/<series>.md`.

## Workflow (9 steps)

1. **Load input** → `python3 scripts/load_input.py` → `.work/chapters.json`
2. **QA proofread** — LLM fixes residual Chinese/English, grammar, clunky MT
   sentences, splits long sentences (moderate, no plot change). Resume-safe per
   chapter. `scripts/assemble_qa.py` writes `.work/chapters_qa.json` (downstream
   source) + `<input>_qa.txt` (TTS file). Always runs.
3. **Bible** — extract (new series) or augment (existing series) the
   `character-bible.md` file. Augment is APPEND-ONLY. Reads the QA'd text.
4. **Genre detect** — sample 3 chapters (first/middle/last) → classify into
   tiên hiệp / huyền huyễn / đô thị / cổ điển / võ hiệp. Refuses đam mỹ /
   ngôn tình.
5. **Style recommend + select** — recommend an art style for the genre (default
   #1 + alternatives) and ask the user to pick (Enter = #1, or type an id);
   `--style <id>` skips the prompt. Headless / no answer → fallback to #1. The
   chosen style is materialized to `.work/active-style.md` and feeds a
   `style_hash` into the scene cache key. Genre and style are decoupled — any of
   the 18 styles works for any genre.
6. **Scene count** — `python3 scripts/calc_scene_count.py` →
   default `images = clamp(round(wc/120), 120, 150)`, `videos = max(20, round(images/6))`;
   CLI overrides are honored exactly.
7. **Scene plan + expand** — LLM writes `.work/scene-plan.md` then per-scene
   `.work/scene-NNN.md` files, using the chosen style for Style + negatives.
   Resume-safe via SHA1 cache (busts when style changes). Two deterministic gates
   guard quality: a **plan gate** (`validate_scene_plan.py`) rejects adjacent
   near-duplicate scenes + fragment synopses (bounded revise loop), and a **depth
   gate** at assembly rejects shallow blocks (missing headers, word count out of
   range, thin negatives, video over 3800 chars) and regenerates them (bounded).
8. **Music prompts** — LLM segments the emotional arc into N mood regions
   (default 4, clamp [3,5]; `--music N` honored verbatim) → one instrumental
   Lyria prompt per region in `.work/music-NNN.md`. Score register follows the
   chosen style's `music/score anchor`. Resume-safe.
9. **Assemble** → `python3 scripts/assemble_outputs.py` writes the image, video,
   and music `.txt` files next to the input.

## Usage

```
/visual-prompt <input.txt> [--series <name>] [--genre <name>] [--style <id>] \
                            [--images N] [--videos M] [--music N] [--epic] [--force-redo]
```

`--style <id>` picks an art style up-front (skips the interactive recommend step);
ids are in `references/style-catalog.md`. Omit it to get a recommendation and
choose interactively. `--music N` sets the exact number of music loops (honored
verbatim, no clamp); omit it for adaptive segmentation (default 4, clamped to [3,5]).
`--epic` amplifies scale — bumps the recommended scene-mix action band one notch
and favors wide spectacle — but still never fabricates combat/armies the story
does not contain (it amplifies real beats only). Best for stories that genuinely
support grand scale.

## Input Spec

- Vietnamese (machine-translated is fine — the QA gate cleans it up; no
  pre-proofread required).
- Chapter markers `Chương 1: …`, `CHƯƠNG 1`, `Chapter 1`, etc. (regex in
  `scripts/load_input.py`)
- Encoding: UTF-8 preferred; fallback chain handles utf-8-sig, gbk, gb18030,
  cp1252.

## Output Spec

- 4 `.txt` files in the same directory as the input:
  - `_qa.txt` — proofread, TTS-ready (chapter headings end with a period so TTS
    pauses; feed to TTS_Local VieNeu / VietVoice).
  - `_image_prompts.txt`, `_video_prompts.txt` — separators `--- SCENE NNN ---`
    (NNN = original scene index; video file shows gaps so indices match images).
  - `_music_prompts.txt` — separators `--- LOOP i / N — Chương X-Y — mood: … ---`.

## Limitations

- Vietnamese input only (QA gate handles MT residue; no pre-proofread needed).
- Supported genres: tiên hiệp, huyền huyễn, đô thị, cổ điển, võ hiệp.
- **Refuses:** đam mỹ (BL romance), ngôn tình (modern romance) — out of scope.
- Text-only output. Reference-image pattern deferred to v2.
- **One style per run.** Styles in the `accent-title-card` / `video-oriented`
  categories keep character identity poorly across many scenes — best for opening
  title cards or montages, not every shot. The recommend step warns when a chosen
  style is in those categories.
- **Headless runs:** the style select step is interactive (CLI foreground). If run
  headless or no answer is given, it falls back to the recommended #1 — use
  `--style <id>` to choose explicitly.
- **Music score register** now follows the chosen style's `music/score anchor`
  (no longer hardcoded). Segmentation/mood logic is unchanged.
- **Lyria music:** prompts are instrumental-only with vocal-exclusion negatives,
  but the model cannot 100% guarantee no vocal-like pads. Region→timeline sync
  is manual — place each loop by its `Chương X-Y` label.
- **Music resume is best-effort:** unlike scenes (fixed `scene-plan.md`), the
  mood-region segmentation is re-derived by the LLM each run and not persisted,
  so a re-run may regenerate music loops if the segmentation shifts. Use
  `--force-redo` for a clean regeneration when in doubt.

## File Layout

```
visual-prompt/
├── SKILL.md                  ← you are here
├── gemini-extension.json
├── commands/visual-prompt.toml
├── prompts/                  ← 9 LLM prompt files (incl. qa-proofread, music-prompt-builder, style-recommender)
├── references/               ← 9 static knowledge files (incl. music-mood-mapping, style-catalog, genre-style-recommendation)
└── scripts/                  ← 7 Python I/O helpers (incl. assemble_qa, validate_scene_plan)
```

See `HUONG-DAN-SU-DUNG.md` for the full Vietnamese user guide.
