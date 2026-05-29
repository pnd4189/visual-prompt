# Brainstorm — Content-Aware Scene Diversity (v0.5)

Date: 2026-05-29 · Skill: visual-prompt · Follows: v0.4 (completed)

## Problem statement

User request: image/video prompts should show more action, more characters in
frame, vast map landscapes, beautiful combat, spell-duels — not just the lone
protagonist. Goal: stop monotonous outputs.

## Scout + verify findings (decisive)

1. **Requirement already in v0.4 spec.** `scene-planner.md` has mix targets
   (action/combat/ritual/reveal 35-45%, wide map 20-30%, multi-char 15-25%);
   `prompt-expander-image.md` task#8 + depth self-check#5; `prompt-expander-video.md`
   task#7; `scene-tag-camera-mapping.md` has combat-map/group/daoist-magic. Adding
   more "combat" wording is redundant.
2. **The thin part1/part2 outputs are NOT pipeline artifacts.** They use
   "1."/"Prompt 1" numbering + 6 fields, no `--- SCENE NNN ---`. Generated outside
   the skill (manual chatbot paste / pre-v04). Not evidence of a pipeline bug.
3. **Structural hole:** quality+diversity rely 100% on the model self-policing
   120-150 iterations. Self-checks are model-honored, not enforced.
   `assemble_outputs.py` only checks presence of `## Image Prompt` — not section
   count, word count, or diversity. Degradation passes silently.
4. **CONTENT verify (decisive):** the source novel is ~22:1 talk:combat
   (combat-vocab hits 14 vs talk/introspection 314 across 10 chapters). It is a
   talky academy tiên hiệp — almost no combat/armies/spell-duels exist in the text.
5. **v0.2 scene-plan artifact** (`tmp_work5`): 0 combat-map/group/daoist-magic tags
   across 116 scenes; synopses are broken mid-sentence fragments ("ùng một gian
   phòng") → garbage input to the expander regardless of expander quality.

## Brutal-honesty conclusion

Monotony is **primarily content-driven**, not a pipeline bug. Forcing a global
35-45% action quota on a talky story makes the model **hallucinate battles not in
the audio** → image/audio mismatch + violates the no-fabrication rule. v0.4's hard
mix targets are wrong as a global default.

## Final agreed solution (v0.5)

1. **Content-aware diversity targets.** Planner measures the story's action
   density first, then sets realistic mix targets. Talky stories get low action
   targets; keep combat/map vocab available for stories/scenes that genuinely have
   it (v0.4 vocab stays).
2. **Anti-monotony for talky stories = VISUAL diversity, not genre diversity:**
   camera/angle/scale variation; group tableaus of characters actually present in
   the scene (legit "more characters", no fabrication); object/detail inserts
   (artifacts, books, talismans mentioned in text); flashback/symbolic shots;
   weather/time-of-day variation. "Vast map" comes from establishing wide shots.
3. **Fix synopsis-fragment bug** (independent, real): planner must emit coherent
   1-line scene synopses, not sliced text fragments. Add a guard.
4. **Two deterministic gates** (user-chosen scope), redefined:
   - **Plan-level:** enforce adjacent-scene variation (reject repeated
     tag+characters+location triples) + synopsis validity (min length,
     non-fragment). NOT a combat percentage.
   - **Assembly-level:** enforce depth — each block has all 10 headers + word
     count in range + negative count ≥ N. Failures → delete that scene-NNN.md,
     regenerate via expander, re-assemble. Loop until clean or max retries.
5. **(Open for plan)** keep an optional `--epic` flag for users who DO want
   amplified scale when the story supports it — hybrid escape hatch.

## Approaches evaluated

| Approach | Verdict |
|---|---|
| A. Deterministic gates + auto-regen | Core — mechanical backstop, closes silent-degradation hole |
| B. Strengthen prompt + few-shot gold example | Adopt as supplement (expander lacks a full example block) |
| C. Chunked volume checkpoints | Cut — cache-resume already eases volume pressure; over-engineer |
| Force global combat quota | Rejected — fabricates plot on talky stories |

## Risks

- Plan-level "variation" check is heuristic on tag+char+location triples — tune
  window (compare within 10 indices) to avoid false rejects.
- Content-density measure must be cheap (keyword scan), not another LLM pass.
- Regeneration loop needs a max-retry cap to avoid infinite loops on hard scenes.
- Few-shot example must be synthetic + copyright-safe (no named IP).

## Success criteria

- Talky-story runs produce visually varied (camera/scale/group/insert) prompts
  with NO fabricated combat.
- Action-heavy stories still get combat/map/spell scenes (v0.4 path intact).
- No two adjacent scenes share tag+characters+location.
- Every assembled image block has 10 sections + word count in range; degraded
  scenes auto-regenerate.
- Synopses are coherent 1-line descriptions, no text fragments.

## Out of scope

New output files, reference-image workflow, new deps, QA/TTS/bible/music
architecture changes.
