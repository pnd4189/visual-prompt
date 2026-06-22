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
   `Style block` and descriptive style vocabulary.
   **SAFETY RULE (hard, all sections):** no brand/logo/trademark name; no real
   public figure / celebrity / "looks like <real person>" likeness; no copyrighted
   IP character or exact branded costume; no nudity/sexual exposure (keep modestly
   clothed); no EXCESSIVE gore (combat/đấu pháp/stylized light blood OK, graphic
   gore not); respect real religion (genre-native cultivation imagery allowed, no
   depicting/desecrating REAL religion); abstract forbidden chapter content.
   **#8 ANIMATION-ONLY (hard):** the video MUST render in the chosen animated /
   illustrated style. ABSOLUTELY no live-action, no photoreal footage, no real
   human face/skin, no deepfake realism (avoid AI-slop / inauthentic-content
   policy). NOTE: the catalog's painterly styles ("semi-realistic digital
   painting", "photo-real lighting", "realistic textures") ARE allowed — the ban
   targets live-action realism, not painterly art.
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
4. Target ~400–600 words, **HARD CAP 3800 characters** (Google Flow / Veo3
   rejects prompts over 4000 chars; 3800 leaves margin for counting drift). The
   char cap is the binding limit — replaces the old 900-word cap.
5. **Audio cue lives in Style & Ambiance**, embedded as diegetic + ambient
   layer. Example: `Audio: steel ringing, low wind through bamboo, distant
   temple bell, no music.` NEVER append `[audio: ...]` as a tag at the end.
6. Hard cap: 3 beats, 8.0s total duration. Veo3 will truncate beyond that.
7. **SPECTACLE BY DEFAULT.** Build motion-rich, cinematic clips: action/combat,
   spell-duels, daoist magic, ritual energy, crowd/army movement, terrain scale,
   spell geometry, weapon impact, debris, cloth motion, ambient reaction. You may
   amplify beyond the literal chapter (add supporting figures, scale, dramatic
   energy) within the genre/identity/continuity rails. NEVER produce a static solo
   portrait clip. (If `mode = faithful`, dramatize only what the text supports.)
8. **PLOT-FIT VARIATION.** The video must animate the scene row's actual focus:
   landscape traversal, faction movement, side-character reaction, chưởng lực
   collision, weapon arc, ritual formation, crowd pressure, artifact reveal, or
   aftermath. Do not convert every video into a protagonist close-up or a generic
   sword draw.

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
5. **Character count (binding)** — count the FULL video block characters. If
   >3800 → trim in this order: (1) Context detail first, (2) Style & Ambiance
   detail second. NEVER drop an action beat or shorten the Identity Anchor. Re-count
   after trimming; must be ≤ 3800 before write.
6. **Depth check** — Action beats use concrete physical motion, Style & Ambiance
   includes lighting/color/audio/safety negatives, and Context includes map scale
   or supporting elements when available.
7. **Safety check (categories 1–8)** — no brand/logo/trademark name; no real
   public figure / celebrity / "looks like <real person>" likeness; no copyrighted
   IP character or exact branded costume; no copied web image or living-artist
   mimicry; no nudity/sexual exposure (modestly clothed); no excessive gore (combat
   OK); respect real religion (fictional cultivation allowed). **#8:** the clip is
   the chosen animated style — NO live-action, NO photoreal footage, NO real human
   face/skin, NO deepfake. Embed these as inline video negatives in the Style &
   Ambiance "avoiding …" clause: `no live-action, no photorealistic footage, no
   real human face or skin, no deepfake realism`. (Painterly "semi-realistic"
   styles stay allowed.) If any violation appears → REWRITE that span.
8. **All 5 sections present** with exact headers `Cinematography:`,
   `Subject:`, `Action:`, `Context:`, `Style & Ambiance:`.
9. **No hero-template check** — If `scene_row.characters` excludes the protagonist
   or includes a group, the Action beats must visibly follow that focus. If the
   beats could fit any chapter after swapping names, REWRITE with concrete motion
   from this scene.

## STDOUT SUMMARY
```
Scene <NNN> video appended: <wc> words, <N> beats, total <S>s
```
