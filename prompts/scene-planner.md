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
- `mode` — `spectacle` (default) | `faithful` from `calc_scene_count.py`
- `action_density` — `low` | `medium` | `high` from `calc_scene_count.py`
- `recommended_mix` — scene-mix band from `calc_scene_count.py` (spectacle band by
  default, e.g. `{action: 25-35%, establishing: 25-35%, group: 20-30%, dialogue_emotional: remainder}`)

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
6. AVOID monotonous protagonist-only portraits (the #1 failure mode). By default
   (spectacle), actively add unnamed supporting groups (disciples, soldiers,
   villagers, guards, beasts, crowds) and large-scale environment/map beats, and
   rotate the focus across side characters and factions — do not let the
   protagonist occupy every frame. Named characters must come from the bible; you
   may freely add UNNAMED groups. (See CINEMATIC AMPLIFICATION below.)

## SCENE MIX TARGETS — SPECTACLE BY DEFAULT

This pipeline feeds YouTube entertainment videos. The DEFAULT register is
**spectacle**: build visually rich, varied, cinematic scenes — wide map-scale
landscapes, multi-character framing, combat, spell-duels (đấu pháp), daoist magic,
grand environments — NOT a string of protagonist close-ups.

Use the `recommended_mix` band passed in INPUT (spectacle band by default):

| Category | Target |
|---|---|
| action / combat / spell-duel / ritual / reveal | `recommended_mix.action` |
| wide environment / map / landscape / establishing | `recommended_mix.establishing` |
| multi-character interaction / group / crowd | `recommended_mix.group` |
| close-up / emotional / dialogue | `recommended_mix.dialogue_emotional` (remainder) |

## CINEMATIC AMPLIFICATION (default directive)

You are ALLOWED — and expected — to DRAMATIZE the story for visual richness, even
beyond what a given chapter states literally. Proactively, across the run:

- **Vast landscapes / maps:** open chapters and transitions with sweeping
  geography — sect mountains, cloud seas, ancient cities, frontiers, secret realms,
  battlefields, star-altars — at map scale, not a single room.
- **More characters in frame:** populate scenes with allies, rivals, sect members,
  elders, disciples, soldiers, crowds, beasts. Do NOT default to the protagonist
  alone. Named characters must come from the bible; you may freely add UNNAMED
  supporting groups to fill and enrich the frame.
- **Combat & spell-duels:** dramatize martial clashes, flying-sword duels, talisman
  formations, qi shockwaves, breakthroughs, artifact reveals, beast battles —
  cinematic and beautiful — wherever the arc can carry them.
- **Vary the focus character:** not every scene centers the protagonist. Feature
  side characters, antagonists, factions, and pure-environment beats.
- **Camera / scale / weather variety:** alternate wide/medium/close, low/high
  angles, dawn/dusk/storm/mist — never repeat the same framing back to back.

**CONSISTENCY RAILS (the only hard limits):** amplification must stay
- **genre-consistent** (xianxia stays xianxia — no Western armor, no modern items);
- **identity-consistent** (named characters use the verbatim bible anchor; do not
  invent named people or change a character's established look);
- **continuity-consistent** (do not contradict explicit stated plot facts — e.g.
  do not show a character the story has killed, or reverse a stated outcome).
Within those rails, dramatize freely. Copyright/likeness safety negatives still
apply (no celebrity face, no copied web image — handled in the expander).

## HARD DIVERSITY QUOTA (validator-enforced — `validate_scene_plan.py`)

The #1 failure is every frame being the protagonist alone. These are NOT
suggestions — the plan gate REJECTS a plan that breaks them and you will be told to
revise:

- **Protagonist presence ≤ 70% of scenes.** At least ~30% of scenes must NOT
  include the protagonist at all — center them on other named characters,
  antagonists, factions, crowds, beasts, or pure environment/map.
- **Solo scenes ≤ 35%.** The majority of scenes have 2+ characters (allies, rivals,
  elders, disciples, soldiers, crowds — named from bible or unnamed groups).
- **No single scene_tag > 35%.** Spread across establishing, group, combat-map,
  daoist-magic, travel, reveal, ritual, dialogue, emotional, action.

Plan the FULL run to satisfy these before writing. A protagonist-locked plan is
invalid output.

**EPIC MODE (`epic = true`):** band arrives bumped one notch — push even harder on
map scale, army/crowd size, and spectacle.

**FAITHFUL MODE (`faithful = true`):** the band is content-aware instead; in this
mode do NOT invent combat/armies absent from the text — draw variety only from
camera/scale, real group tableaus, object inserts, and weather shifts. (Spectacle
is the default; faithful is the opt-in for documentary-style accuracy.)

Video flags prioritize the most motion-rich, spectacular scenes: combat, chases,
spell formations, breakthroughs, crowd/army movement, map-scale traversal, and
major openers/climaxes. Flag exactly `videos_m` scenes, and by default this means
at least 20.

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

For plan-wide violations (`scene_ids` empty), REBALANCE the whole plan, not single
rows:
- `protagonist_overspotlight` → convert enough protagonist scenes into ones centered
  on other named characters, antagonists, factions, crowds, or pure environment so
  the protagonist drops to ≤70% presence.
- `too_many_solo` → add characters/groups to enough solo scenes to get solo ≤35%.
- `tag_monotony` → re-tag enough scenes (establishing/group/combat-map/daoist-magic/
  travel/reveal) so no tag exceeds 35%.

Keep changes grounded in the chapters' world (spectacle dramatization allowed; do
not break genre/identity/continuity). Re-run the self-checks, then rewrite
`.work/scene-plan.md`.

## STDOUT SUMMARY
```
Scene plan written: .work/scene-plan.md
Total scenes: <N> (<M> flagged for video)
Video indices: <comma-sep list>
Chapters covered: 1..<K>
```
