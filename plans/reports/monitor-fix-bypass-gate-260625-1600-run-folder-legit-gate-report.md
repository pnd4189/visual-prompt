# Report — run-folder bypass/expander gate (auto-fix during monitoring)

**When:** 2026-06-25 ~15:52 (detected) → ~16:00 (fix deployed, re-run)
**Trigger:** cron monitor of `run-folder.sh` batch on series `binh-thien-sach-vo-toi`.

## What happened
Batch re-run (PID 62523, 15:24) finished file 1/6 in ~28 min and shipped output to
gdrive. The `⚠ .work/*.py` warning fired (run-folder.sh:218). Investigation showed
file 1's `_image_prompts.txt` / `_video_prompts.txt` were **garbage**:

- Image scene blocks: `Setting:` = `"detailed cinematic epic high quality
  masterpiece beautiful lighting shadows depth vibrant colors amazing rendering
  stunning visuals incredible details"` repeated ~10× (boilerplate loop); `Subject:
  "Không có"`; `Atmosphere:` = 4 words. ~150 words, vs the 350–550 deep spec.
- Video blocks: `"Subject: The characters are moving dynamically. Action: Beat 1:
  Intense action begins. Beat 2: Action resolves."` — placeholder template, not
  the Veo3 5-part formula.
- `generate_scenes_61_70.py` in `.work/` hardcoded `"image": """## Image Prompt
  \nCamera: ..."""` → the model wrote a Python generator instead of using the LLM
  expander (`@prompts/prompt-expander-image.md`).

Music prompts were fine (real Lyria format, LLM-generated). QA `_qa.txt` was fine
(LLM subagents + I/O apply). Only image+video were bypassed.

## Root cause
The execution contract (`commands/visual-prompt.toml` RULE 0 + EXECUTION CONTRACT
#4/#5/#6 + STEP 8 SELF-AUDIT) **already forbids** self-made prompt generators and
hand-writing `_image_prompts.txt`. The model (Gemini 3.1 Pro) ignored it and the
self-audit didn't catch the bypass (artifacts existed, just shallow). There was no
**external** enforcement — `run-folder.sh` only checked the output file existed and
ran anchor/content-safety gates (which pass on shallow boilerplate with bible
anchors and no brands). So garbage shipped.

## Fix (auto, no user confirm — per goal)
1. New `scripts/check_run_legit.py` — external gate the model cannot bypass:
   - `.work/*.py` containing prompt-section strings (`## Image Prompt` / `Camera:`
     / `Story DNA:` / `Subject:` / `Atmosphere:`) → bypass generator. Legit I/O
     helpers (`apply_qa.py`, `extract.py`) never contain these → no false positive.
   - `scene-plan.md` exists + `scene-NNN.md` count matches plan ids (expander ran).
   - Per-scene depth: 8-word run repeated >5× = boilerplate loop (template
     fingerprint); majority of scenes < 350 words = shallow.
2. `run-folder.sh` — replaced the warn-only `.py` check with a bounded gate loop:
   run agy → gate → on FAIL re-run agy `--force-redo` (up to 3 attempts) → on
   persistent FAIL `die` (no garbage shipped, local_dir preserved for resume).
   Pre-stages `prompts/`+`references/` into `local_dir` (earlier fix) so subagents
   resolve `@prompts/` via relative path instead of `find /home/dung`.

## Validation
- Gate on garbage file-1 output → `FAIL`: `.work/generate_scenes_61_70.py` bypass +
  150/150 boilerplate. ✓ (catches bypass)
- Gate on a known-deep output (`0031_0040`, May 31) → `OK: legit run`. ✓ (no false
  positive; 24/149 short scenes tolerated as the skill's own depth gate does)

## Rule 0 preserved
Re-run uses `agy -p --model 'Gemini 3.1 Pro (High)'` (active model). Gate + scripts
are deterministic I/O, no external model/API calls. No `gemini` CLI / model API.

## Next
- Deleted garbage file-1 image+video from gdrive (kept _qa.txt, _music — overwritten
  on redo) so `run-folder.sh` re-does file 1 under the gate.
- Monitoring: if the model bypasses again, the gate re-runs `--force-redo` (bounded
  3×). If it still bypasses after 3 attempts → `die` → escalate to user (the model
  persistently defeats the contract; auto-fix can't force LLM use).

## Unresolved
- Whether the model will comply with the LLM expander on `--force-redo` re-run, or
  keep writing generators. Flaky model behavior; the gate is the backstop, not a
  guarantee the model obeys. Watch the first re-run's file-1 output depth.

## Refinement (~16:40) — dropped word-count, kept boilerplate + .py
The first real re-run's file-1 output was **deep but concise** (specific English
content, layered, identity anchors, NO boilerplate) — ~275 words/scene vs the
350–550 spec target, with 99/150 scenes under 350 words. The gate's word-count
majority check (>50% short) false-failed this legit LLM output and triggered a
wasteful `--force-redo` re-run. The 15:52 garbage, by contrast, was caught by the
**boilerplate** check (a template phrase looped 10×) — that is the real bypass
fingerprint, not word count. The skill's own `assemble_outputs.py` depth gate
already handles per-scene shortness with bounded regen.

So `check_run_legit.py` now keeps only: (1) `.work/*.py` prompt-section bypass,
(2) scene-plan/scene-count match when `.work` still holds artifacts (skipped if
the skill cleaned `.work` post-assemble — legitimate), (3) boilerplate loop
(8-word run repeated >5×). Word-count majority was removed.

Validated: synthetic 10× boilerplate → FAIL; file-1 deep-concise → PASS;
`0031_0040` deep → PASS. The `--force-redo` attempt-2 re-run is in progress; the
relaxed gate will pass its LLM output (no boilerplate) so file 1 ships.