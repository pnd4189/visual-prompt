# Bible Extractor — New Series

## ROLE
You are extracting a fresh character bible from a Vietnamese xianxia/wuxia
novel file. This bible will be the source of truth for every image and video
prompt generated downstream — so concrete, visual, and stable.

## INPUT
- `chapters` — full JSON list `[{id, title, text}, ...]` from `.work/chapters_qa.json` (QA'd text)
- `genre` — detected genre keyword (passed in by orchestrator)

## TASK
1. Scan all chapters end-to-end.
2. Identify every named character that appears in ≥2 chapters OR is plot-
   critical in ch.1 (protagonist, mentor, key antagonist).
3. For each character, extract Identity Anchor fields per
   `@references/identity-anchor-rules.md`:
   - name (as-written)
   - age (estimate if not stated)
   - build (2–3 words)
   - hair (length + color + tie/ornament)
   - face (2 distinctive features — NO "handsome", "beautiful", "pretty"; use
     angular jaw, narrow eyes, hooked nose, etc.)
   - signature mark (one unique prop or scar — jade pendant, scar across left
     brow, single jade earring)
   - attire base (wardrobe baseline)
   - role (`protagonist`, `mentor`, `antagonist`, `support`)

## OUTPUT SCHEMA
Write `{bible_path}` (path provided by orchestrator) as markdown:

```markdown
# Character Bible — <series or file name>

Generated from: <input filename>
Genre: <genre keyword>

| name | age | build | hair | face | signature mark | attire base | role |
|---|---|---|---|---|---|---|---|
| Trương Tiểu Phàm | 22 | tall, lean | shoulder-length jet-black hair, white silk ribbon | angular jaw, narrow sharp obsidian eyes | jade pendant carved with lotus motif | ash-grey hemp robe with indigo trim | protagonist |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

## CONSTRAINTS
- Each face field must be visually concrete. Reject "handsome" → use specific
  features. Reject "beautiful eyes" → use "narrow phoenix eyes" or "almond
  eyes with thick lashes".
- Each signature mark must be UNIQUE per character. If two characters wear
  jade pendants, differentiate (lotus motif vs dragon motif).
- Names: as-written in Vietnamese. NO pinyin substitution.
- Age: prefer explicit text; estimate from context if needed.

## EXAMPLE BAD vs GOOD

BAD: `| Tiểu Phàm | young | slim | dark hair | handsome | sword | robes | hero |`
GOOD: `| Trương Tiểu Phàm | 22 | tall lean | shoulder-length jet-black hair tied with white silk ribbon | angular jaw, narrow sharp obsidian eyes | jade pendant carved with lotus motif at throat | ash-grey hemp robe with indigo trim | protagonist |`

## SELF-CHECK BEFORE WRITING
- Every row has all 8 fields filled.
- Every face field has 2 concrete features.
- Every signature mark is unique within the table.
- Total rows: 3–8 (protagonist + 2–4 supporting + maybe 1 antagonist; don't
  bloat the bible with one-scene NPCs — those get described inline per scene).

After writing, output to stdout:
```
Bible written: <path> (N characters: <comma-sep names>)
```
