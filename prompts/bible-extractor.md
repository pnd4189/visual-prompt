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
2. Identify every named character who may appear in a planned visual beat. Do not
   enforce a minimum or maximum row count.
3. For each character, extract Identity Anchor fields per
   `@references/identity-anchor-rules.md`:
   - name (as-written)
   - age (exact source statement, otherwise `not stated`)
   - build (source description, otherwise `not stated`)
   - hair (source description, otherwise `not stated`)
   - face (source description, otherwise `not stated`)
   - signature mark (source-stated recurring prop/scar, otherwise `not stated`)
   - attire base (source-stated wardrobe, otherwise `not stated`)
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
- Every concrete field must be traceable to a specific statement in
  `.work/chapters_qa.json`. Never derive appearance from genre, role, name,
  personality, or a visual-style default.
- Preserve vague source wording instead of upgrading it. If the source only says
  "young" or "handsome", keep that wording; do not convert it into a number,
  angular jaw, eye shape, hair ornament, scar, or prop.
- Never invent a unique signature mark. Two characters may share a generic
  source-stated item; consistency is not permission to differentiate them.
- Names: as-written in Vietnamese. NO pinyin substitution.
- Unknown fields use exactly `not stated`; do not guess.

## EXAMPLE BAD vs GOOD

BAD: `| Tiểu Phàm | 22 | tall lean | shoulder-length black hair | angular jaw | jade pendant | grey robe | protagonist |`
when the source only names him.

GOOD: `| Tiểu Phàm | not stated | not stated | not stated | not stated | not stated | not stated | protagonist |`

## SELF-CHECK BEFORE WRITING
- Every row has all 8 fields filled; unknown values are exactly `not stated`.
- For every non-`not stated` visual field, re-open the QA chapter and verify the
  wording is supported. If no exact support can be located, replace it with
  `not stated`.
- No age estimate, inferred face/build, invented costume, or synthetic signature
  mark remains.
- Row count follows the named characters in the source, never a target quota.

After writing, output to stdout:
```
Bible written: <path> (N characters: <comma-sep names>)
```
