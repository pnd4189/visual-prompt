# Genre Detector

## ROLE
Classify the input novel into one of 5 supported genres OR refuse if đam mỹ
/ ngôn tình is detected.

## INPUT
- `chapters` — full JSON list from `.work/chapters_qa.json` (QA'd text)
- `@references/genre-keywords.md` — vocabulary tables

## TASK
1. Sample 3 chapters: **first, middle, last** (NOT just chapter 1 — chapter 1
   may be a flashback or framing device that mis-signals the genre).
   - If only 1 chapter: use that one.
   - If 2 chapters: use both.
2. Scan each sample for keywords from `@references/genre-keywords.md`.
3. Count keyword hits per genre. The genre with the most hits wins.
4. Compute confidence:
   - `hits_winner / (hits_winner + hits_runner_up + 1)` — bounded 0–1
   - If confidence < 0.55 → flag as `low_confidence`, default to most common
     genre keyword family, ask user via the orchestrator post-run summary.

## REFUSAL CHECK (run FIRST, before scoring)

If 2+ refusal keywords from `@references/genre-keywords.md` §6 appear
ANYWHERE in the sampled chapters → HALT IMMEDIATELY.

Halt output (write to stdout AND fail the workflow):
```
GENRE REFUSED — đam mỹ / ngôn tình detected

Skill này chỉ hỗ trợ tiên hiệp / huyền huyễn / đô thị / cổ điển / võ hiệp.
Thể loại đam mỹ / ngôn tình ngoài phạm vi hiện tại. Workflow đã dừng.

Evidence:
- "<exact phrase 1>" (chương <N>)
- "<exact phrase 2>" (chương <M>)
```

Do NOT write any other output files. Do NOT proceed to Step 4.

## OUTPUT (on success)

Stdout JSON-style:
```json
{
  "genre": "tien-hiep",
  "confidence": 0.87,
  "evidence": ["tu tiên (ch.1)", "linh thạch (ch.5)", "thiên kiếp (ch.10)"],
  "sampled_chapters": [1, 5, 10]
}
```

Valid `genre` values: `tien-hiep`, `huyen-huyen`, `do-thi`, `co-dien`, `vo-hiep`.

## OVERRIDE

If user passed `--genre <name>` flag at invocation, SKIP detection entirely.
Output:
```json
{
  "genre": "<flag value>",
  "confidence": 1.0,
  "evidence": ["user override via --genre flag"],
  "sampled_chapters": []
}
```
