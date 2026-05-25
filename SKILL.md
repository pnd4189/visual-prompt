---
name: visual-prompt
version: 0.2.0
description: Generate cinematic 4K image + video prompts, a QA'd TTS-ready text, and Lyria music prompts from Vietnamese xianxia/wuxia novel files for YouTube audio videos
license: MIT
contextFileName: SKILL.md
---

# Visual Prompt Skill

LLM-driven workflow that reads a Vietnamese xianxia/wuxia novel file
(.txt / .md / .docx, 2k–18k words, suitable for a 1–2h audio video). The skill
self-QAs the text first (no pre-proofread required), then emits four
paste-ready files:

- `<input>_qa.txt` — proofread, TTS-ready source of truth (residual Chinese/
  English removed, grammar fixed, long sentences split). Feed straight into
  TTS_Local (VieNeu / VietVoice).
- `<input>_image_prompts.txt` — hybrid 200–300 word sectioned image prompts
  (Camera / Setting / Subject / Style / Lighting / Negative) for Gemini, Qwen,
  ChatGPT, etc.
- `<input>_video_prompts.txt` — Google Veo3 5-part formula video prompts
  (Cinematography → Subject → Action `[00:00–00:02.5]` → Context →
  Style & Ambiance, audio embedded as scene layer).
- `<input>_music_prompts.txt` — instrumental Lyria 3 music prompts, one per
  mood region of the story arc (default 4, `--music N` override).

## Philosophy

- **LLM is the loop driver.** Gemini Ultra reads input, plans scenes, writes
  prompts. Python only handles I/O the model can't do safely.
- **QA-first.** A proofread gate runs before everything else and produces the
  single QA'd source of truth that all downstream steps (bible, genre, scenes,
  music) consume. The skill no longer assumes pre-proofread input.
- **Reuses proven I/O scripts** from `chinese-novel-proofreader` v3.6.
- **Character bible verbatim.** Identity Anchor is pasted byte-for-byte into
  every scene so the same character looks the same across all images.
- **Cross-file series support** via `--series <name>` flag — bible persists in
  `~/.gemini/bibles/<series>.md`.

## Workflow (8 steps)

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
5. **Scene count** — `python3 scripts/calc_scene_count.py` →
   default `images = round(wc/200)`, `videos = round(images/7)`; CLI overrides.
6. **Scene plan + expand** — LLM writes `.work/scene-plan.md` then per-scene
   `.work/scene-NNN.md` files. Resume-safe via SHA1 cache.
7. **Music prompts** — LLM segments the emotional arc into N mood regions
   (default 4, clamp [3,5]; `--music N` honored verbatim) → one instrumental
   Lyria prompt per region in `.work/music-NNN.md`. Resume-safe.
8. **Assemble** → `python3 scripts/assemble_outputs.py` writes the image, video,
   and music `.txt` files next to the input.

## Usage

```
/visual-prompt <input.txt> [--series <name>] [--genre <name>] \
                            [--images N] [--videos M] [--music N] [--force-redo]
```

`--music N` sets the exact number of music loops (honored verbatim, no clamp).
Omit it for adaptive segmentation (default 4, clamped to [3,5]).

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
├── prompts/                  ← 8 LLM prompt files (incl. qa-proofread, music-prompt-builder)
├── references/               ← 7 static knowledge files (incl. music-mood-mapping)
└── scripts/                  ← 6 Python I/O helpers (incl. assemble_qa)
```

See `HUONG-DAN-SU-DUNG.md` for the full Vietnamese user guide.
