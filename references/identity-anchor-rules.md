# Identity Anchor Rules — Character Bible

> Related: [[visual-prompt-template]] · [[genre-keywords]]

The single most important rule for character consistency across all images
and videos: **paste the Identity Anchor verbatim** into every prompt's
Subject section. Do NOT paraphrase.

## Why Verbatim (not rewrite)?

Empirical test (research R2, 2026):
- Verbatim Identity Anchor across 10 scenes → **8.5/10** face/clothing consistency
- LLM-rewritten variant per scene → **5–6/10** drift (hair length changes, eye
  color flips, robe color shifts).

The image model latches onto the exact word string. Even synonyms ("dark hair"
vs "jet-black hair") produce different faces. Treat the anchor as a hash.

## Bible Row Schema

`character-bible.md` is a markdown table. One row = one character. Columns:

| Field | Required? | Format | Example |
|---|---|---|---|
| name | yes | as-written in novel | `Trương Tiểu Phàm` |
| age | yes | integer | `22` |
| build | yes | 2-3 word phrase | `tall, lean` |
| hair | yes | length + color + tie | `shoulder-length jet-black hair, tied with white silk ribbon` |
| face | yes | 2 distinctive features | `angular jaw, narrow sharp obsidian eyes` |
| signature mark | yes | one unique prop or scar | `jade pendant carved with lotus motif at throat` |
| attire base | yes | wardrobe baseline | `ash-grey hemp robe with indigo trim` |
| role | yes | 1 word | `protagonist`, `mentor`, `antagonist`, `support` |

## Identity Anchor Block (the verbatim string)

Concatenate fields into ONE prose block. This is what gets pasted into every
Subject section.

**Format:**
```
<name> — <age> years old, <build> build, <hair>, <face>, <signature mark>,
<attire base>.
```

**Example:**
```
Trương Tiểu Phàm — 22 years old, tall lean build, shoulder-length jet-black
hair tied with a single white silk ribbon, angular jaw, narrow sharp obsidian
eyes, small jade pendant carved with lotus motif at the throat, ash-grey
hemp robe with indigo trim.
```

This exact block goes into EVERY image/video prompt's Subject section. After
the verbatim block, you may append scene-specific state (pose, expression,
wardrobe condition for this shot — e.g. "robe hem mud-streaked from travel").

## BAD Example (don't do this)

Scene 1 Subject: `A young cultivator with dark hair and sharp eyes wears a grey robe.`
Scene 2 Subject: `Tiểu Phàm, late twenties, raven hair, intense gaze, in his usual robes.`
Scene 3 Subject: `The protagonist, slim and tall, hair flowing, in monk attire.`

Result: three different faces. Each scene is "a young man" not "this specific
man." YouTube viewer notices instantly.

## GOOD Example (do this)

Every scene Subject starts with the **exact same** Identity Anchor block
above, then varies only the **after-comma** state portion.

## Augmentation Rule (cross-file series)

When processing a 2nd, 3rd, ... file in the same series with an existing bible:

1. Read existing bible rows.
2. Identify characters in new chapters NOT in bible.
3. For each new character: call `python3 scripts/append_bible_row.py --bible <path> --row <new-row>` — APPEND ONLY.
4. **NEVER edit existing rows**, even if the new chapter describes the
   character slightly differently. The first description wins for series
   consistency. Log discrepancies to `.work/bible-conflicts.md` for user
   review.

Why: changing an existing row → all previous file's prompts now point at an
outdated anchor; image consistency breaks for the whole series.

## Bible Storage Location

- Per-file (default): `<input-dir>/character-bible.md`
- Per-series (with `--series <name>`): `~/.gemini/bibles/<name>.md`
