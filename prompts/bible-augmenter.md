# Bible Augmenter — Existing Series

## ROLE
A new file in an existing series is being processed. A `character-bible.md`
already exists. Your job: identify NEW characters in the new chapters and
**append** rows for them. NEVER edit existing rows.

## INPUT
- `chapters` — full JSON list from `.work/chapters_qa.json` (the NEW file, QA'd text)
- `bible_path` — path to existing `character-bible.md`
- `genre` — detected genre

## TASK
1. Read the existing bible. Note all character names already present.
2. Scan new chapters for character names.
3. For each source-named character not in the existing bible who may appear in a
   visual beat, extract Identity Anchor fields per
   `@references/identity-anchor-rules.md`. Every concrete field must be supported
   by the new QA chapters; write exactly `not stated` for unknown age, build,
   hair, face, signature mark, or attire. Never estimate or visually complete a
   character from genre, role, or name.
4. For each new character, call:
   ```bash
   python3 scripts/append_bible_row.py --bible <bible_path> --row '<full markdown table row>'
   ```
   The script appends only — existing rows stay byte-identical.

## CRITICAL CONSTRAINT — DO NOT MODIFY EXISTING ROWS

Even if a new chapter describes an existing character slightly differently
(e.g. "his hair is now grey from sorrow" vs original "shoulder-length jet-
black hair"), DO NOT change the existing row. The first description wins
for series consistency. The image model needs the same anchor across all
files of the series.

If a contradiction is significant (e.g. completely different name, gender
swap, age leap >10 years), log it to `.work/bible-conflicts.md`:

```markdown
# Bible Conflicts — <new file name>

## <character name>
- Bible says: <existing description excerpt>
- New chapter says: <new description excerpt> (chapter <N>)
- Resolution: kept bible verbatim. User review recommended.
```

But still DO NOT modify the bible.

Before appending each row, re-open the relevant QA passage. If a concrete visual
field cannot be traced to the source, replace it with `not stated`. Do not invent
a unique prop or alter vague wording to improve image consistency.

## OUTPUT TO STDOUT
```
Bible augmented: <bible_path>
New rows appended: <N>
New characters: <comma-sep names>
Existing rows untouched: <M>
Conflicts logged: <K> (see .work/bible-conflicts.md)
```

## SELF-CHECK BEFORE FINISHING
- Run `wc -l <bible_path>` before and after. Difference = exactly N (new rows).
- For 2 random existing rows: confirm byte-identical to pre-run state (the
  append-only script guarantees this, but verify if you suspect bug).
- If you used the Write tool on `bible_path` directly (instead of
  `append_bible_row.py`) → STOP, that violates the contract. Revert and
  redo via the script.
