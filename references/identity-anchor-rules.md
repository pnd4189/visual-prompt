# Identity Anchor Rules — Character Bible

> Related: [[visual-prompt-template]] · [[genre-keywords]]

The single most important rule for character consistency across all images
and videos: **paste the Identity Anchor verbatim** into every prompt's
Subject section. Do NOT paraphrase.

## Why Verbatim (not rewrite)?

Repeated exact identity wording reduces face, hair, and clothing drift. Treat the
anchor as a hash, but never improve consistency by inventing the hash's contents.
Source truth has priority over visual completeness.

## Bible Row Schema

`character-bible.md` is a markdown table. One row = one character. Columns:

| Field | Required? | Format | Example |
|---|---|---|---|
| name | yes | as-written in novel | `Trương Tiểu Phàm` |
| age | yes | exact source wording or `not stated` | `22` |
| build | yes | source wording or `not stated` | `tall, lean` |
| hair | yes | source wording or `not stated` | `shoulder-length black hair` |
| face | yes | source wording or `not stated` | `narrow eyes` |
| signature mark | yes | source-stated recurring prop/scar or `not stated` | `jade pendant` |
| attire base | yes | source-stated wardrobe or `not stated` | `ash-grey hemp robe` |
| role | yes | 1 word | `protagonist`, `mentor`, `antagonist`, `support` |

## Identity Anchor Block (the verbatim string)

Concatenate fields into ONE prose block. This is what gets pasted into every
Subject section.

**Format when every field is stated:**
```
<name> — <age> years old, <build> build, <hair>, <face>, <signature mark>,
<attire base>.
```

For every `not stated` field, use the literal clause `age not stated`, `build not
stated`, `hair not stated`, `face not stated`, `signature mark not stated`, or
`attire not stated`. If age is vague source wording rather than a number, use
`age described as <source wording>`. Do not silently fill the gap. Example:

```
Tiểu Phàm — age not stated, build not stated, black hair, face not stated,
signature mark not stated, grey robe.
```

**Example:**
```
Trương Tiểu Phàm — 22 years old, tall lean build, shoulder-length jet-black
hair tied with a single white silk ribbon, angular jaw, narrow sharp obsidian
eyes, small jade pendant carved with lotus motif at the throat, ash-grey
hemp robe with indigo trim.
```

This exact block goes into every image/video prompt that includes the character.
After it, append only scene-specific state supported by the current QA chapter.
Do not infer pose, expression, or wardrobe condition merely to make the anchor
more visual.

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
4. **NEVER edit existing rows** automatically, even if the new chapter describes
   the character differently. Log discrepancies to `.work/bible-conflicts.md`
   for user review; do not resolve them by guessing.

Why: changing an existing row → all previous file's prompts now point at an
outdated anchor; image consistency breaks for the whole series.

## Bible Storage Location

- Per-file (default): `<input-dir>/character-bible.md`
- Per-series (with `--series <name>`): `~/.gemini/bibles/<name>.md`
