# Video Prompt Expander — Per Video-Flagged Scene

## ROLE
For scenes where `flag_for_video = ✓` in scene-plan, append a `## Video Prompt`
block to the existing `.work/scene-<NNN>.md` (created by `prompt-expander-image.md`).
Format: Google Veo3 official 5-part formula.

## INPUT (per video scene)
- `scene_row` — same as image expander
- `bible` — `character-bible.md` (filter to characters in scene)
- `genre` — detected genre
- `chapter_excerpt` — relevant chapter text ONLY
- `active_style` — `.work/active-style.md` content (one chosen style entry)
- existing `.work/scene-<NNN>.md` — image prompt is already there

## TASK
1. Load `@references/visual-prompt-template.md` (video format section) AND
   `.work/active-style.md`. The `Style & Ambiance` section uses the active style's
   `Style block` + its `reference anchors`; do NOT inject a fixed cinema reference.
2. Load `@references/scene-tag-camera-mapping.md` — pick row matching
   `scene_row.scene_tag` for Cinematography defaults.
3. Build the prompt with these EXACT sections in order:
   ```
   Cinematography: ...
   Subject: <IDENTITY ANCHOR VERBATIM> + shot-specific state
   Action:
   [00:00-00:02.5] beat 1
   [00:02.5-00:05.0] beat 2
   [00:05.0-00:08.0] beat 3 (or omit if 2-beat scene)
   Context: ...
   Style & Ambiance: ...
   ```
4. Target 400–800 words. Hard cap 800.
5. **Audio cue lives in Style & Ambiance**, embedded as diegetic + ambient
   layer. Example: `Audio: steel ringing, low wind through bamboo, distant
   temple bell, no music.` NEVER append `[audio: ...]` as a tag at the end.
6. Hard cap: 3 beats, 8.0s total duration. Veo3 will truncate beyond that.

## ACTION BEAT RULES
- Each beat: ONE concrete physical action (step, turn, draw, strike, gaze).
- Timestamps are ms-precision in format `[MM:SS-MM:SS.x]`.
- Total duration ≤ 8.0s.
- 2 beats OK for slower scenes (ritual, emotional). 3 beats max.
- Do NOT change camera shot type between beats — Veo3 handles ONE sustained
  camera movement per clip cleanly. Cuts within 8s look glitchy.

## IDENTITY ANCHOR — SAME RULE AS IMAGE
Paste verbatim from bible. Self-check char-by-char before write.

## OUTPUT — APPEND to existing scene file

Read existing `.work/scene-<NNN>.md`. Append the video block:

```markdown
## Video Prompt

Cinematography: ...

Subject: <verbatim anchor> ... <shot-specific state>

Action:
[00:00-00:02.5] ...
[00:02.5-00:05.0] ...
[00:05.0-00:08.0] ...

Context: ...

Style & Ambiance: ... Audio: <diegetic + ambient>, no music.
```

Use the Write tool to overwrite the file with image block + video block
(or any safe append method).

## MANDATORY SELF-CHECK BEFORE WRITE

1. **Identity Anchor verbatim** (same as image — char-by-char compare).
2. **Duration check** — last timestamp end ≤ `00:08.0`. If >8.0 → trim or
   merge beats.
3. **Beat count** — 2 or 3 beats. Not 1, not 4+.
4. **Audio location** — `Audio:` appears INSIDE Style & Ambiance line, NOT
   as a separate trailing tag.
5. **Word count** — body ≤ 800 words.
6. **All 5 sections present** with exact headers `Cinematography:`,
   `Subject:`, `Action:`, `Context:`, `Style & Ambiance:`.
7. **Style reference** — the chosen style's `reference anchors` (from
   `.work/active-style.md`) appears in Style & Ambiance. No fixed cinema reference
   unless it IS the chosen style's anchor.

## STDOUT SUMMARY
```
Scene <NNN> video appended: <wc> words, <N> beats, total <S>s
```
