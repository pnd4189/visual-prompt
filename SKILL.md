---
name: visual-prompt
version: 0.16.7
description: Generate grounded, non-repetitive image prompts by default, with explicitly enabled video/music prompts, strict source anchors, parent-only generation, and fail-closed quality gates for Vietnamese xianxia/wuxia novel files; the batch driver may opt into isolated runner-level Pass-2 workers (VP_WORKERS) and may scope runs via VP_NO_VIDEO/VP_NO_MUSIC/VP_GLOB without changing the default serial run or the default workflow; the auto scene band runs 120-300 images (a ~3h narration); the plan gate checks every declared total against its source — image and chapter counts recomputed from the chapter JSON, genre against genre.txt, per-chapter coverage against each chapter's share of the prose; lean Setting/Action are length-checked per micro-batch (8-word floor) so a stub field fails on the first scenes instead of as a duplicate flood at the end; the stop gate refuses to end a run whose .work has no chapters_qa.json or plan.hash, and scene-plan.md cannot be written before chapters_qa.json exists, so the pipeline cannot be skipped down to the scene plan; Style is checked as the series lock — one block repeated verbatim, since the repetition gate deliberately never compares it
license: MIT
contextFileName: SKILL.md
---

# Visual Prompt Skill

LLM-driven workflow (Antigravity/Agy, Codex, or Claude Code) that reads a Vietnamese xianxia/wuxia novel file
(.txt / .md / .docx, 2k–18k words, suitable for a 1–2h audio video). The skill
self-QAs the text first (no pre-proofread required), then emits QA + image
prompts. Video and music files are opt-in:

- `<input>_qa.txt` — proofread, TTS-ready source of truth (residual Chinese/
  English removed, grammar fixed, long sentences split). Feed straight into
  TTS_Local (VieNeu / VietVoice).
- `<input>_image_prompts.txt` — deep 350–550 word sectioned image prompts
  (Camera / Story DNA / Setting / Composition / Subject / Action-Energy /
  Style / Lighting-Color / Atmosphere / Negative).
- `<input>_video_prompts.txt` — optional deep Veo3 5-part formula video prompts
  (Cinematography → Subject → Action `[00:00–00:02.5]` → Context →
  Style & Ambiance, audio embedded as scene layer).
- `<input>_music_prompts.txt` — optional instrumental Lyria 3 music prompts, one
  per mood region of the story arc (`--music` or `--music N`), written as
  gentle emotional background underscore for narration, each block using a
  Chap-5-style `prompt paragraph + Tags:` structure and targeting a 2-3 minute
  seamless background loop.

## Philosophy

- **Active parent model owns generation.** The active model on Agy, Codex, or
  Claude reads input, plans scenes, writes every prompt, and runs self-checks.
  No subagent, team, delegation, parallel writer, external CLI, model API, or
  second LLM may create or rewrite creative content. Python only handles
  deterministic I/O and validation. See `references/strict-generation-contract.md`.
  Sole exception (runner-level, opt-in): `scripts/run-folder.sh` may spawn
  isolated worker sessions of this same skill via `VP_WORKERS` +
  `--worker-manifest` for Pass-2 scene expansion. Each worker is itself the
  parent model for its disjoint scene range — RULE 0 binds every worker
  session (no nested delegation), and direct invocations never use worker mode.
- **Agy runtime authorship is enforced, not merely instructed.** The guard loads
  from the global `~/.gemini/config/hooks.json` and from the imported plugin's
  `hooks.json` (so every event fires twice — the guard is idempotent), arms
  on the user's `/visual-prompt` turn and blocks delegation/background tools,
  runtime generators, non-canonical commands, and non-primary writes. Every Agy
  scene write records content-hash provenance; final and worker gates reject
  missing, secondary-agent, or stale hashes, and the `Stop` gate refuses to end a
  run whose legitimacy gate still fails (bounded to 2 holds, never a loop). The
  restricted `visual-prompt-writer` primary agent plus `VP_WORKERS` keeps bounded
  parallel generation fast without permitting nested writers.
- **Parent-only micro-batches.** Generate at most three scene files per creative
  turn, verify them, then continue. If quota or context runs out, stop at a
  resumable scene ID; never switch to a scripted generator.
- **Deep prompt quality is mandatory.** Enabled image/video/music prompts must
  include layered story DNA, character/prop locks, source-supported environment,
  foreground/
  midground/background composition, lighting/palette, action/energy/audio, and
  negative/safety rules. Shallow prompts are invalid.
- **Content-safety is enforced (8 categories).** Outputs must avoid brands/logos,
  real public figures, copyrighted IP characters, copied images/artworks, excessive
  gore, sexual/nudity, and disrespect of real religion; VIDEO must be the chosen
  animation style (no live-action / photoreal footage). Soft prevention lives in
  the expanders/planner; a deterministic gate (`scripts/check_content_safety.py` +
  `references/blocklist-content-safety.md`) strips/softens at STEP 7 and re-scans at
  STEP 8. Combat/đấu pháp and fictional cultivation imagery stay allowed; religion
  is WARN-and-ship.
- **Grounded creativity by default.** QA'd chapter text and the character bible
  lock every story fact. Each scene has an exact source anchor. Creativity is
  required in truthful visual realization — camera, composition, setting detail,
  action phase, lighting, palette, texture, and atmosphere — but never by adding
  characters, crowds, combat, locations, props, weather, or outcomes.
- **Image-only by default.** Every run produces QA + image prompts. Video requires
  `--video`, `--videos N`, or an explicit video request. Music requires `--music`,
  `--music N`, or an explicit music request. `--no-video` and `--no-music` win.
- **Plot-fit staging, including truthful stillness.** When the source describes a
  landscape, render it richly without adding scale, landmarks, weather, or people.
  When characters are present, stage only their source-supported action or
  interaction. A quiet, solitary, or motionless beat stays quiet; make it visually
  distinct through camera, composition, focus, light, and palette rather than
  inventing activity.
- **Diversity is grounded, not quota-forced.** `validate_scene_plan.py` verifies
  source anchors, chapter membership, synopsis uniqueness, and adjacent
  setting/camera/action/palette variation. It never forces a new character or
  event merely to satisfy a ratio.
- **Repetition is outcome-gated.** Plan synopses and assembled image,
  video, and music prompts are checked across the full run. Targeted rewrites use
  deterministic violation ids, while per-series visual history discourages exact
  camera, setting, action, music-intro, and tag reuse across later files.
- **The skill dir is read-only for the agent.** `scripts/` holds exactly
  the `CANONICAL_SCRIPTS` allowlist versioned inside `check_run_legit.py`; the
  agent must never create or edit files under the skill dir (scratch goes only to
  `.work/`). Any non-canonical file in `scripts/`
  or stray code file at the skill root — the fingerprint of a self-made bypass
  generator hiding under a helper-looking name — fails the external gate, and
  `run-folder.sh` auto-quarantines it into `.quarantine-auto/` before each
  attempt. STEP 8's self-audit runs the same gate (`check_run_legit.py`).
- **Original outputs only.** Do not copy web images, famous faces, celebrity
  likenesses, known-character faces, or exact IP/artist styles.
- **QA-first.** A proofread gate runs before everything else and produces the
  single QA'd source of truth that all downstream steps (bible, genre, scenes,
  music) consume. The skill no longer assumes pre-proofread input.
- **Cross-file continuity first.** Before QA, the workflow checks whether the
  first chapter in the current file follows the previous chapter from nearby
  `_qa.txt` / `.txt` files. A likely skipped, repeated, or non-continuing chapter
  halts the run instead of being hidden by proofreading.
- **Reuses proven I/O scripts** from `chinese-novel-proofreader` v3.6.
- **Character bible verbatim.** Identity Anchor is pasted byte-for-byte into
  every scene so the same character looks the same across all images.
- **Cross-file series support** via `--series <name>` flag — bible persists in
  `~/.gemini/bibles/<series>.md`.

## Workflow (10 steps)

1. **Load input** → `python3 scripts/load_input.py` → `.work/chapters.json`
2. **Cross-file continuity audit** — `scripts/check_previous_continuity.py`
   finds the previous chapter file and the model compares previous tail vs current
   opening for skipped/repeated/non-continuing chapters.
3. **QA proofread** — LLM fixes residual Chinese/English, grammar, clunky MT
   sentences, splits long sentences (moderate, no plot change). Resume-safe per
   chapter. `scripts/assemble_qa.py` writes `.work/chapters_qa.json` (downstream
   source) + `<input>_qa.txt` (TTS file). Always runs.
4. **Bible** — extract (new series) or augment (existing series) the
   `character-bible.md` file. Augment is APPEND-ONLY. Reads the QA'd text.
5. **Genre detect** — sample 3 chapters (first/middle/last) → classify into
   tiên hiệp / huyền huyễn / đô thị / cổ điển / võ hiệp. Refuses đam mỹ /
   ngôn tình.
6. **Style recommend + select** — recommend an art style for the genre (default
   #1 + alternatives) and ask the user to pick (Enter = #1, or type an id);
   `--style <id>` skips the prompt. Headless / no answer → fallback to #1. The
   chosen style is materialized to `.work/active-style.md` and feeds a
   `style_hash` into the scene cache key. Genre and style are decoupled — any of
   the 18 styles works for any genre.
7. **Scene count** — `python3 scripts/calc_scene_count.py` →
   default `images = clamp(round(wc/120), 120, 300)`, `videos = 0`; video count is
   calculated only after an explicit `--video`/`--videos N`. The ceiling covers a
   ~3h narration (~37k words). `validate_scene_plan.py` checks the plan's declared
   totals against their sources rather than against itself — image count and
   chapter count recomputed from the chapter JSON, genre against `.work/genre.txt`,
   and per-chapter coverage against each chapter's share of the prose. It writes
   `.work/plan.hash` once the plan passes.
8. **Scene plan + expand** — active parent model writes `.work/scene-plan.md` then
   per-scene `.work/scene-NNN.md` files in micro-batches of ≤3. Source-anchor,
   artifact, depth, and similarity gates fail closed.
9. **Optional media** — only when explicitly enabled, write video/music artifacts;
   disabled media is not loaded, generated, validated, assembled, or reported.
10. **Assemble** → `python3 scripts/assemble_outputs.py` writes enabled outputs
    next to the input; final gates run before completion.

## Usage

```
/visual-prompt <input.txt> [--series <name>] [--genre <name>] [--style <id>] \
                            [--images N] [--video] [--videos M] [--music [N]] \
                            [--epic] [--faithful] [--no-video] [--no-music] [--force-redo]
```

`--style <id>` picks an art style up-front (skips the interactive recommend step);
ids are in `references/style-catalog.md`. Omit it to get a recommendation and
choose interactively. `--video` enables adaptive video count; `--videos M` enables
exactly M. `--music` enables adaptive music segmentation (3–5 regions);
`--music N` enables exactly N. Natural-language requests after the command are
equivalent explicit opt-ins. `--epic` may intensify only source-supported visual
realization. `--faithful` is retained as a compatibility alias; all runs are
grounded. `--no-video`/`--no-music` disable their medium.

**Batch driver (runner-level).** `scripts/run-folder.sh` stays serial by default.
Opt-in `VP_WORKERS=N` (N ≥ 2, capped by remaining scene rows) enables bounded
parallel Pass-2 only: a `--plan-only` head session, isolated worker sessions on
disjoint scene-ID ranges over a frozen snapshot, a fail-closed join, then the
serial tail (music/assemble/gates). Workers never publish history, markers, or
assembled outputs; all final gates stay coordinator-only; any failure falls back
to the unchanged serial path. Direct `/visual-prompt` invocations never use
worker mode. Rollback = unset `VP_WORKERS` and restart the driver.
The driver also accepts per-run scopes without changing the default workflow:
`VP_NO_VIDEO=1` / `VP_NO_MUSIC=1` skip that medium for the run (gates, harness
waits, completion manifest, and visual-history extract all switch with the flag;
music-enabled resumes are never invalidated), and `VP_GLOB` selects the input
filename pattern (default `*.txt`, e.g. `*_vi.txt` for translation-only folders).
Batch mode otherwise keeps opting into music and video as before.

## Input Spec

- Vietnamese (machine-translated is fine — the QA gate cleans it up; no
  pre-proofread required).
- Chapter markers `Chương 1: …`, `CHƯƠNG 1`, `Chapter 1`, etc. (regex in
  `scripts/load_input.py`)
- Encoding: UTF-8 preferred; fallback chain handles utf-8-sig, gbk, gb18030,
  cp1252.

## Output Spec

- By default, 2 `.txt` files in the same directory as the input:
  - `_qa.txt` — proofread, TTS-ready (chapter headings end with a period so TTS
    pauses; feed to TTS_Local VieNeu / VietVoice).
  - `_image_prompts.txt` — separators `--- SCENE NNN ---`.
- With `--video`/`--videos N`, add `_video_prompts.txt`.
- With `--music`/`--music N`, add `_music_prompts.txt`; each block is an English
  paragraph followed by `Tags:`.

## Limitations

- Vietnamese input only (QA gate handles MT residue; no pre-proofread needed).
- Supported genres: tiên hiệp, huyền huyễn, đô thị, cổ điển, võ hiệp.
- **Refuses:** đam mỹ (BL romance), ngôn tình (modern romance) — out of scope.
- Text-only output. Reference-image pattern deferred to v2.
- **Optional media flags:** `--video`/`--videos N` enable video; `--music`/`--music N`
  enable music. `--no-video` and `--no-music` explicitly disable them and are
  honored by the planner, expanders, assemblers, and validators. The batch driver
  opts in explicitly when its `VP_MUSIC`/`VP_NO_VIDEO` settings request it.
- **One style per run.** Styles in the `accent-title-card` / `video-oriented`
  categories keep character identity poorly across many scenes — best for opening
  title cards or montages, not every shot. The recommend step warns when a chosen
  style is in those categories.
- **Headless runs:** the style select step is interactive (CLI foreground). If run
  headless or no answer is given, it falls back to the recommended #1 — use
  `--style <id>` to choose explicitly.
- **Music score register** follows the chosen style's `music/score anchor`, but
  every prompt is softened into instrumental background underscore for story
  narration.
- **Lyria music:** prompts are instrumental-only with vocal-exclusion negatives,
  but the model cannot 100% guarantee no vocal-like pads. Each block is one
  English music prompt paragraph followed by `Tags:`; region→timeline sync is
  manual via the `.work/music-NNN.md` frontmatter.

## File Layout

```
visual-prompt/
├── SKILL.md                  ← you are here
├── gemini-extension.json
├── commands/visual-prompt.toml
├── prompts/                  ← 9 LLM prompt files (incl. qa-proofread, music-prompt-builder, style-recommender)
├── references/               ← 11 static knowledge files (incl. strict generation contract, style catalog, safety blocklist)
├── hooks.json                ← Agy active-model runtime guard wiring
├── agents/visual-prompt-writer/agent.md ← restricted primary Agy writer
└── scripts/                  ← deterministic helpers + 2 batch drivers; the exact list is the CANONICAL_SCRIPTS allowlist in check_run_legit.py — anything else in scripts/ is treated as a bypass artifact
```

See `HUONG-DAN-SU-DUNG.md` for the full Vietnamese user guide.
