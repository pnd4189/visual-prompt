# Scene Planner — Pass 1

## ROLE
Read the entire novel + bible + genre → produce a flat ordered list of N
distinct scenes covering the full narrative arc, with M of them flagged for
video expansion.

## INPUT
- `chapters` — full JSON list
- `bible` — `character-bible.md` content
- `genre` — detected genre keyword
- `images_n` — total image count target (default auto path: 120–150)
- `videos_m` — total video count target (default auto path: at least 20)
- `action_density` — `low` | `medium` | `high` from `calc_scene_count.py`
- `recommended_mix` — content-aware scene-mix band from `calc_scene_count.py`
  (e.g. `{action: 5-15%, establishing: 25-35%, group: 20-30%, dialogue_emotional: remainder}`)

## TASK
1. Read all chapters in order. Identify the narrative arc: setup, rising
   action, climax(es), resolution.
2. Allocate ~N scenes proportionally across the arc:
   - Establishing scenes (first chapter, new locations): wide shots
   - Action / climax scenes: motion shots, combat, pursuit, weapon impact
   - Daoist magic / ritual scenes: formations, talismans, breakthrough, artifacts
   - Wide map scenes: city, sect, battlefield, mountain range, frontier, secret realm
   - Multi-character scenes: allies, enemies, sect groups, armies, crowds
   - Dialogue / emotional: close-ups
   - Travel / transition: lateral tracking
3. For each scene, fill: scene_id, chapter_ref, scene_tag, characters_present,
   synopsis_1line, flag_for_video.
4. **Flag exactly M scenes** for video. Pick from: openers, climaxes,
   action-dense, ritual reveals, big travel montages. NEVER flag pure
   dialogue or static meditation.
5. Distribute scenes ROUGHLY evenly across chapters (don't dump 30 scenes
   into chapter 1 and 2 into chapter 10).
6. For high-count runs, avoid monotonous protagonist-only portraits. If chapter
   context supports it, include unnamed supporting groups (disciples, soldiers,
   villagers, guards, beasts) and large-scale environment beats. Named characters
   must come from bible/chapter; do not invent named people.

## SCENE MIX TARGETS — CONTENT-AWARE

Use the `recommended_mix` band passed in INPUT. It is derived from the story's
measured `action_density`, so a talky story gets a LOW action target and a
combat-heavy story keeps the high band. Do NOT impose a fixed 35–45% action quota
on every run — that is the high-density band only.

| Category | Target |
|---|---|
| action / combat / ritual / reveal | `recommended_mix.action` |
| wide environment / map / establishing | `recommended_mix.establishing` |
| multi-character interaction / group | `recommended_mix.group` |
| close-up / emotional / dialogue | `recommended_mix.dialogue_emotional` (remainder) |

Hit the action band by drawing on scenes that GENUINELY have action in the text.
If the chapters do not contain combat/armies/spell-duels, do NOT fabricate them to
fill a quota — draw anti-monotony from VISUAL VARIETY instead (next section).

## VISUAL-VARIETY RULE (anti-monotony without fabrication)

When a story is talky (low action_density), variety comes from how you SHOOT what
is actually in the chapter — never from invented battles. Vary across the run:

- **Camera / scale:** alternate wide establishing, medium two-shots, close-up
  inserts, low/high angles, over-the-shoulder — do not repeat the same framing.
- **Group tableaus of characters ACTUALLY present:** when a chapter has multiple
  people in a scene, frame them together (sect hall, classroom, gathering) instead
  of a lone portrait. Only people the chapter places there.
- **Object / detail inserts:** named props from the text (a book, talisman, jade
  pendant, brewing pot, letter) as their own macro/detail shot.
- **Flashback / symbolic shots:** a memory or symbolic image the chapter implies.
- **Weather / time-of-day shifts:** dawn, dusk, rain, mist, lamplight — vary the
  environment beat across nearby scenes.

**NO-FABRICATION GUARD (hard):** never add combat, armies, spell-duels, weapons,
or crowds that the referenced chapter does not contain. Amplifying framing of real
content is allowed; inventing plot events is forbidden.

**EPIC MODE (`epic = true`):** `recommended_mix` already arrives bumped one notch.
Favor wide establishing shots, larger group tableaus of characters actually
present, and grander scale cues for the beats the story DOES have. The
NO-FABRICATION GUARD still holds above this note — epic amplifies real scenes, it
never invents battles or armies absent from the chapter.

Video flags prioritize the most motion-rich scenes the story ACTUALLY has: for an
action story that means combat/chase/spell/breakthrough; for a talky story that
means the liveliest real beats (a reveal, a heated exchange, a journey, a ritual,
a weather event, a meaningful gesture). Flag exactly `videos_m` scenes, and by
default this means at least 20.

## SCENE TAGS (must be one of)
`establishing`, `action`, `combat-map`, `daoist-magic`, `group`, `dialogue`,
`reveal`, `emotional`, `ritual`, `travel`

(Maps to camera defaults via `@references/scene-tag-camera-mapping.md`.)

## SYNOPSIS RULE (mandatory)

`synopsis` is ONE grammatical sentence describing WHAT is visually happening in
the shot, written in your own words from the chapter's meaning. It is NOT a copied
substring of the chapter text.

- Must read as a complete clause (subject + action), not a sliced fragment.
- Must NOT start mid-word or mid-sentence (no leading lowercase fragment like
  "và rồi hắn", no dangling "…phòng").
- Describe the visible moment (who, doing what, where), ~6–20 words.

**Self-check:** if a synopsis looks like a raw text slice (starts lowercase
mid-word, has no clear subject+verb, or is a truncated phrase) → rewrite it as a
coherent one-line description before writing the file.

## OUTPUT
Write `.work/scene-plan.md`:

```markdown
# Scene Plan — <input filename>

Genre: <genre> · Images: <N> · Videos: <M> · Chapters: <K>

| scene_id | chapter | scene_tag | characters | synopsis | video? |
|---|---|---|---|---|---|
| 001 | 1 | establishing | Trương Tiểu Phàm | Tiểu Phàm đứng trên đỉnh Linh Sơn, gió thổi, kiếm trong tay | ✓ |
| 002 | 1 | dialogue | Trương Tiểu Phàm, Phổ Hồng | Phổ Hồng hỏi Tiểu Phàm đã sẵn sàng xuống núi chưa | |
| 003 | 2 | travel | Trương Tiểu Phàm | Đi qua thác nước, rừng trúc khi mặt trời lặn | |
| ... | ... | ... | ... | ... | ... |
```

## UNIQUENESS SELF-CHECK (mandatory before write)

Scan your own table. For every pair of scenes within 10 indices of each other:
- If they share >70% of characters AND same scene_tag AND similar location/
  setting → REVISE one of them (change scene_tag, change focus character, OR
  drop and reuse the index for a different moment).
- If three nearby rows are all "one character stands / gazes / walks" → REVISE
  at least two into action, map, group, ritual, object-detail, or aftermath beats
  grounded in the chapter.

Repeat until 0 near-duplicate pairs remain.

## DISTRIBUTION CHECK

- Total scenes = `images_n` (exact).
- Video-flagged scenes = `videos_m` (exact).
- Per-chapter scene count: `images_n / chapters` ± 30% tolerance.

If any check fails → revise before writing the file.

## REVISE-FLAGGED CONTRACT (retry path)

When the plan validation gate (`validate_scene_plan.py`) reports violations, you
will be asked to revise ONLY the flagged `scene_ids` — keep every other row byte
for byte. Re-emit the full table with just those rows fixed:

- `adjacent_duplicate` → change the flagged row's `scene_tag`, OR shift its focus
  character / framing so it no longer repeats its neighbor (a real, distinct beat
  from the same chapter — no fabrication).
- `fragment_synopsis` → rewrite that row's `synopsis` as one coherent sentence per
  the SYNOPSIS RULE (no raw text slice, starts with a capital, subject + verb).

Do not renumber, reorder, or drop unflagged rows. Re-run the self-checks, then
rewrite `.work/scene-plan.md`.

## STDOUT SUMMARY
```
Scene plan written: .work/scene-plan.md
Total scenes: <N> (<M> flagged for video)
Video indices: <comma-sep list>
Chapters covered: 1..<K>
```
