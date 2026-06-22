---
phase: 1
title: "Hard gate core (script + blocklist)"
status: completed
priority: P1
dependencies: []
effort: ""
---

# Phase 1: Hard gate core (script + blocklist)

## Overview
Build the deterministic content-safety gate: a Python scanner that finds and
(with `--fix`) strips blocklisted brand/person/IP/gore/sexual/religion content in
the assembled prompt files, plus its data file. Mirrors
`scripts/check_anchor_consistency.py` (argparse, scan→fix→report, exit 0/2/1).

## Requirements
- Functional: detect 8 categories (incl. #8 photoreal/live-action video);
  `--fix` replaces offending span with a neutral
  generic; report counts per category; exit 0 clean / 2 violations remain / 1 IO.
- Non-functional: pure stdlib (re, argparse, pathlib); no external model/network
  (RULE 0); case-insensitive whole-word literal match; regex only fires with
  trigger words to avoid false positives.

## Architecture
Two new files:

### `references/blocklist-content-safety.md` (data)
Markdown with one `## SECTION` per category; the script parses lines under each.
Line conventions: plain line = literal token (case-insensitive whole-word);
`re: <pattern>` = regex. Sections:
- `## BRANDS` — curated global + Chinese brands (literals). e.g. Nike, Adidas,
  Apple, iPhone, Samsung, Coca-Cola, Pepsi, Starbucks, McDonald's, Louis Vuitton,
  Gucci, Chanel, Rolex, Disney, Marvel, Genshin Impact, Honkai.
- `## IP_CHARACTERS` — common franchise/character names (literals). e.g. Naruto,
  Goku, Pikachu, Mickey Mouse, Iron Man, Elsa.
- `## LIKENESS_TRIGGERS` — regex, fire only with trigger + a following name:
  `re: (?i)\b(?:looks like|resembles|in the style of|cosplay of|portrait of|modeled on|giống|trông giống|theo phong cách|mô phỏng)\b\s+["']?[A-ZÀ-Ỹ][\wÀ-ỹ.'-]+(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ.'-]+)*`
- `## GORE` — regex/literals: `re: (?i)\b(decapitat\w*|disembowel\w*|dismember\w*|entrails|gushing blood|blood splatter|mutilat\w*|torture\w*|gore)\b`, plus VN `máu me, chặt đầu, moi ruột, phanh thây`.
- `## SEXUAL` — regex/literals: `re: (?i)\b(nude|naked|nudity|topless|bottomless|sexual|erotic|lingerie|cleavage|seductive|provocative)\b`, plus VN `khỏa thân, hở hang, gợi dục, khiêu dâm`.
- `## RELIGION_HIGH_RISK` — literals (WARN-only): Prophet Muhammad, Muhammad,
  Allah (as depicted figure), Jesus Christ, Buddha (as real worship target +
  desecration), plus desecration regex `re: (?i)\b(desecrat\w*|burning (?:the )?(?:quran|bible|torah)|blasphem\w*)\b`. WARN, do NOT auto-rewrite (context-sensitive).
- `## PHOTOREAL_VIDEO` — regex, ban live-action / real-human realism (#8). MUST be
  precise to avoid false-positives on painterly styles in `style-catalog.md`
  (`semi-realistic-digital-painting`, `painterly-realism-cinematic`,
  `concept-art-cityscape` "photo-real lighting", `photobash-epic-poster`
  "realistic textures"). Match ONLY strong signals:
  `re: (?i)\b(live[- ]action|photoreal(?:istic)? (?:footage|video|render)|hyperrealistic|real human (?:actor|face|skin)|filmed (?:footage|scene)|deepfake|DSLR photo|8k photograph)\b`.
  Do NOT match bare `realistic`, `semi-realistic`, `photo-real lighting`,
  `realistic textures`. Fix → replace with `<chosen animated style>` /
  `stylized animation`.

### `scripts/check_content_safety.py` (logic)
```
usage: check_content_safety.py --output <prompts.txt> --blocklist <md> [--fix]
exit: 0 = clean (or all auto-fixable fixed), 2 = violations remain, 1 = IO/parse
```
Functions (mirror anchor script shape):
- `parse_blocklist(text) -> dict[str, dict]` → `{section: {literals:[...], regexes:[compiled]}}`.
- `scan(text, rules) -> dict[str, list[hit]]` → hits per category (span, matched).
- `fix_text(text, rules) -> tuple[str, int]` → apply replacements:
  - BRANDS/IP_CHARACTERS: delete the matched token (and a trailing ` logo`/` brand`).
  - LIKENESS_TRIGGERS: drop the matched trigger+name clause.
  - GORE: replace match → `no graphic blood`.
  - SEXUAL: replace match → `modestly clothed`.
  - RELIGION_HIGH_RISK: NOT fixed — collected for WARN, contributes to exit 2.
- `main()`: if `--fix`, write back + print `content-safety-fix: stripped N`. Then
  scan; print per-category WARN lines for residual; return 2 if any residual
  (incl. religion), else 0. Religion always reported as WARN even after fix.

## Related Code Files
- Create: `scripts/check_content_safety.py`
- Create: `references/blocklist-content-safety.md`
- Reference (pattern to mirror, do not modify here): `scripts/check_anchor_consistency.py`

## Implementation Steps
1. Write `references/blocklist-content-safety.md` with the 6 parseable sections
   above + a short header explaining the line conventions.
2. Write `check_content_safety.py`: argparse, `parse_blocklist`, `scan`,
   `fix_text`, `main`; stdlib only; same exit-code contract as anchor script.
3. Make literal matching case-insensitive + whole-word (`\b...\b`), keep the
   brand list conservative to limit false positives.
4. Implement `--fix` replacements per the mapping; religion = WARN-only.
5. Smoke test (manual, see Success Criteria) — no pytest in repo, use crafted
   temp files.

## Success Criteria
- [ ] Crafted sample containing `Nike`, `looks like Jackie Chan`, `gushing blood`,
      `topless` → `--fix` strips/softens all four; re-scan (no `--fix`) exits 0.
- [ ] Sample with fictional name `Hàn Lập` and `Daoist temple, incense, cultivation
      aura` → scan exits 0 (no false positive; name has no trigger, temple not blocked).
- [ ] Sample with `Prophet Muhammad` → reported as WARN, exit 2 even with `--fix`
      (not auto-rewritten).
- [ ] Video sample with `live-action footage` / `real human actor` → flagged +
      fixed to stylized animation; sample with `semi-realistic digital painting` /
      `photo-real lighting` → NOT flagged (no false positive).
- [ ] Script uses only stdlib; `python3 scripts/check_content_safety.py -h` works.

<!-- Updated: Validation Session 1 - added PHOTOREAL_VIDEO section (#8) + precise carve-out for painterly styles -->
<!-- Updated: Validation Session 1 - confirmed religion WARN-only, brand case-insensitive whole-word -->


## Risk Assessment
- False positives on brand literals that are common words → keep list curated;
  whole-word + case-insensitive; document extensibility.
- Auto-strip can leave slightly awkward sentence → acceptable per chosen
  auto-strip+WARN policy; mapping kept natural.
- Regex over VN diacritics → ensure UTF-8 read and Unicode-aware classes.
