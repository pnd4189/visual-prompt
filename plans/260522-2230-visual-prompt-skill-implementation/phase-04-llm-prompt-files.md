---
phase: 4
title: "LLM Prompt Files"
status: done
priority: P1
effort: "1.5d"
dependencies: [3]
---

# Phase 4: LLM Prompt Files

## Overview

The actual workflow brain. 6 prompt files implement steps 2-5 of the `/visual-prompt` flow (bible extract/augment, genre detect, scene plan, image expand, video expand). Each file is a self-contained instruction set the LLM loads + executes; references from Phase 3 provide format/vocab; Python scripts from Phase 2 wrap I/O. Also fills the stub `commands/visual-prompt.toml` from Phase 1.

## Context Links

- Brainstorm §3 (workflow), §4 (prompt files), §6 (LLM responsibilities)
- Phase 3 references (loaded via `@references/<name>.md` syntax)
- Phase 2 scripts (called via `python3 scripts/<name>.py ...`)
- Reference pattern: `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/prompts/*.md`

## Requirements

**Functional:**
- `bible-extractor.md`: read input chapters → emit `{input_dir}/character-bible.md` with Identity Anchor rows (or augment existing)
- `bible-augmenter.md`: read existing bible + new chapters → append new characters, NEVER edit/delete existing rows (preserves cross-file series consistency)
- `genre-detector.md`: read 2-3 sample chapters → output detected genre keyword + confidence; refuse if đam mỹ/ngôn tình
- `scene-planner.md`: read full input + bible + genre → emit `.work/scene-plan.md` (table of N scenes with: id, chapter ref, scene tag, 1-line synopsis, characters present); enforce uniqueness self-check (no 2 scenes too similar)
- `prompt-expander-image.md`: per scene → emit `.work/scene-NNN.md` with `## Image Prompt` block (hybrid 200-300 word sectioned, identity anchor verbatim, 3-layer negative)
- `prompt-expander-video.md`: per video scene → emit `.work/scene-NNN.md` with `## Video Prompt` block (Google 5-part, ms-timestamps, audio as scene layer)
- `commands/visual-prompt.toml`: full 6-step prompt orchestrating all of the above

**Non-functional:**
- Each prompt file <250 lines (LLM context budget)
- Resume-safe: each scene-NNN.md atomic-written; rerun skips existing files unless `--force-redo`
- Idempotent: rerunning entire workflow on same input produces same output (modulo LLM nondeterminism, which is bounded by structured prompts)

## Architecture

```
prompts/
├── bible-extractor.md         # Step 2a (new series, no bible)
├── bible-augmenter.md         # Step 2b (existing bible, new file)
├── genre-detector.md          # Step 3
├── scene-planner.md           # Step 4 (Pass 1)
├── prompt-expander-image.md   # Step 5a (per-scene image)
└── prompt-expander-video.md   # Step 5b (per-scene video)

commands/
└── visual-prompt.toml         # Top-level orchestrator (filled in this phase)
```

Workflow when `/visual-prompt input.txt` invoked:
```
0. Parse + validate flags (--series, --genre, --images, --videos, --force-redo)
   Reject unknown flags with clear VN error; print parsed values for user visibility
1. python3 scripts/load_input.py → .work/chapters.json
   Compute SHA1(input.txt) → .work/input.hash (for cache invalidation in Step 6)
2. if {input_dir}/character-bible.md exists: @prompts/bible-augmenter.md
     LLM emits new rows ONLY via `python3 scripts/append_bible_row.py --bible ... --row ...`
   else: @prompts/bible-extractor.md writes fresh bible
   Compute SHA1(character-bible.md) → .work/bible.hash
3. @prompts/genre-detector.md (sample first+middle+last chapter)
4. python3 scripts/calc_scene_count.py → {images_n, videos_m}
5. @prompts/scene-planner.md → .work/scene-plan.md (N total scenes, M flagged for video)
   Compute SHA1(scene-plan.md) → .work/plan.hash
6. for each scene in scene-plan:
     if .work/scene-NNN.md exists AND not --force-redo:
       read frontmatter cache_key from scene-NNN.md
       expected_key = SHA1(input.hash + bible.hash + plan.hash + scene_row_text)
       if cache_key == expected_key: skip (cache valid)
       else: WARN "scene NNN stale (input/bible/plan changed) — regenerating" + regenerate
     else: generate scene-NNN.md
   Each scene-NNN.md has frontmatter:
     ---
     scene_id: NNN
     cache_key: <sha1>
     has_video: true|false
     ---
     ## Image Prompt
     <hybrid 200-300 word sectioned block>
     ## Video Prompt   (only if scene flagged for video)
     <Google 5-part block>
7. python3 scripts/assemble_outputs.py → 2 final .txt files
```

## Related Code Files

### Create
- `prompts/bible-extractor.md` (~150 lines): instructions to scan chapters for distinct characters; extract Identity Anchor fields (name, age, build, hair, face, signature mark, attire base, role); output YAML table format defined in `@references/identity-anchor-rules.md`; write to `{input_dir}/character-bible.md`
- `prompts/bible-augmenter.md` (~120 lines): load existing bible; identify new characters in chapters not in bible; APPEND rows only — explicit "DO NOT MODIFY EXISTING ROWS even if descriptions in new chapters differ slightly" rule with WHY (cross-file series consistency)
- `prompts/genre-detector.md` (~100 lines): load `@references/genre-keywords.md`; sample first + middle + last chapter (not just chapter 1, avoid flashback misread); match keywords; output `{genre: "tien-hiep", confidence: 0.9, evidence: ["cụm từ X từ chương 2", ...]}`; if đam mỹ/ngôn tình detected → halt workflow with refusal message in Vietnamese
- `prompts/scene-planner.md` (~200 lines): load full chapters JSON + bible + genre + scene counts; produce markdown table `.work/scene-plan.md` with cols [scene_id, chapter_ref, scene_tag, characters_present, synopsis_1line, flag_for_video]; enforce uniqueness self-check (instruction: "scan your own table — if 2 scenes within 5 indexes have >70% overlap in characters+tag+location, revise one")
- `prompts/prompt-expander-image.md` (~180 lines): per-scene input (scene row + bible + genre + relevant chapter text); load `@references/visual-prompt-template.md` + `@references/scene-tag-camera-mapping.md` + `@references/negative-lists.md`; output `## Image Prompt\n\n<sectioned 200-300 word block>` with sections (Camera/Setting/Subject[verbatim identity anchor]/Style/Lighting/Negative); cite Crouching Tiger or Hero in Style for xianxia/võ hiệp
- `prompts/prompt-expander-video.md` (~200 lines): per-video-scene input; load same refs + Google 5-part formula; output `## Video Prompt\n\n<5-part block>` with subsections [Cinematography / Subject (verbatim anchor) / Action (timestamped `[00:00-00:02.5]` x 2-3 beats, max 8s total) / Context / Style & Ambiance (audio cue embedded here, not appended)]
- `commands/visual-prompt.toml` (FULL — replaces Phase 1 stub): description + prompt orchestrating all 6 steps with conditional branches (bible exists?, scene file cache valid?, genre allowed?); handles `--series`, `--genre`, `--images`, `--videos`, `--force-redo` flags via explicit Step 0 FLAG PARSE block (LLM regex-extracts each flag from `{{args}}` string, validates, echoes parsed values back to user before proceeding — eliminates silent flag-typo failures per red-team #5)

### Modify
- `commands/visual-prompt.toml` — Phase 1 wrote stub; this phase writes full 6-step orchestrator

### Delete
- (none)

## Implementation Steps

1. **Write `bible-extractor.md`**: structure as ROLE → INPUT → TASK → OUTPUT SCHEMA → CONSTRAINTS → EXAMPLE; constraints include "Identity Anchor must be visually concrete (no 'handsome' — use 'angular jaw, narrow eyes, single jade earring')"; output schema cites `@references/identity-anchor-rules.md` for YAML row format
2. **Write `bible-augmenter.md`**: same structure; CRITICAL constraint section "PRESERVE EXISTING ROWS VERBATIM — append-only; if new chapter contradicts existing description, log conflict to `.work/bible-conflicts.md` but do not change bible"
3. **Write `genre-detector.md`**: sample 3 chapters not 1 (avoid flashback bias from R2 risk row); output JSON-style; refusal block for đam mỹ/ngôn tình includes Vietnamese user message: "Skill này chỉ hỗ trợ tiên hiệp/huyền huyễn/đô thị/cổ điển/võ hiệp. Thể loại đam mỹ/ngôn tình ngoài phạm vi hiện tại."
4. **Write `scene-planner.md`**: include uniqueness self-check pseudocode; enforce `flag_for_video` count matches `--videos M` (cap, no exceeding); flag rule: video for openers, climax, action-dense, ritual reveals — never for pure dialogue scenes
5. **Write `prompt-expander-image.md`**: include 1 full INPUT→OUTPUT example in-prompt; emphasize "paste Identity Anchor BLOCK VERBATIM from bible into Subject section — do NOT paraphrase"; **mandatory self-check at end of output**: LLM must echo back the Identity Anchor block char-for-char and compare to bible source — if mismatch, regenerate; negative list construction: append universal + genre + style from `@references/negative-lists.md` (cap 20 items); **chapter excerpt rule** (red-team #14): load ONLY the chapter referenced by scene_row.chapter_ref, NOT full chapters.json (avoids context overflow on 18k-word files)
6. **Write `prompt-expander-video.md`**: include 1 full example with ms-timestamps `[00:00-00:02.5][00:02.5-00:05.0][00:05.0-00:08.0]`; Action section limited to 3 beats max 8s total per R2; Audio cue in Style & Ambiance using format `Audio: <natural diegetic sound>, <emotional ambient>` — NOT as appended `[audio: ...]` tag
7. **Write `commands/visual-prompt.toml`** (replaces Phase 1 stub): description = "Generate cinematic 4K image+video prompts from Vietnamese xianxia novel files for YouTube audio videos"; prompt structure:
   - **STEP 0 (FLAG PARSE)** — explicit block: extract `--series <val>`, `--genre <val>`, `--images <N>`, `--videos <M>`, `--force-redo` from `{{args}}` using regex patterns shown inline; validate (N/M positive int; series matches `[a-z0-9-]+`; genre in allowlist); echo parsed values to user in VN: "Đã nhận flags: series=X, genre=Y, ..."; on unknown flag → halt with VN error
   - **STEP 1-7** — workflow per architecture diagram above (with hash-based cache invalidation in Step 6)
   - **POST-RUN summary** — list output file paths + counts (N image, M video) + bible location + any warnings (stale-cache regenerations, scene file skips)
8. **Wire `--series <name>` flag**: when present, bible path = `~/.gemini/bibles/<series>.md` (shared across files in series); when absent, bible path = `{input_dir}/character-bible.md` (per-file)
9. **Add `--force-redo` flag handling** in `visual-prompt.toml`: if set, delete `.work/scene-*.md` before Step 6 loop
10. **Test each prompt file in isolation**: paste it into Antigravity + sample input → verify output format matches spec
11. **End-to-end dry-run** on a 3-chapter sample (Phase 5 will do full test)

## Todo List

- [ ] `prompts/bible-extractor.md` written + isolated test passes
- [ ] `prompts/bible-augmenter.md` written + isolated test (verify append-only)
- [ ] `prompts/genre-detector.md` written + tested with xianxia sample + đam mỹ refusal sample
- [ ] `prompts/scene-planner.md` written + uniqueness self-check verified
- [ ] `prompts/prompt-expander-image.md` written + output matches Phase 3 template
- [ ] `prompts/prompt-expander-video.md` written + ms-timestamps + audio as scene layer verified
- [ ] `commands/visual-prompt.toml` filled with 6-step orchestrator (replaces stub)
- [ ] `--series`, `--genre`, `--images`, `--videos`, `--force-redo` flags wired

## Success Criteria

- [ ] Running `/visual-prompt <sample.txt>` in Antigravity executes all 6 steps without manual intervention
- [ ] `bible-extractor` output is paste-able verbatim into `prompt-expander-image` Subject section
- [ ] `genre-detector` correctly classifies 5 sample xianxia files (none misread as đô thị)
- [ ] `scene-planner` produces non-duplicate scenes (manual review: 0 pairs >70% overlap in 50-scene plan)
- [ ] Image prompt output: 200-300 words, 5-6 sections, Crouching Tiger or Hero cited (xianxia/võ hiệp), 3-layer negatives
- [ ] Video prompt output: 5-part structure, ms-precision timestamps, audio embedded in Style & Ambiance
- [ ] `--force-redo` clears `.work/scene-*.md` before re-running
- [ ] đam mỹ sample → workflow halts with Vietnamese refusal message

## Risk Assessment

| Risk | Mitigation |
|---|---|
| LLM ignores "verbatim Identity Anchor" rule and paraphrases | Add 2 bad/good examples in `prompt-expander-image.md` + mandatory char-for-char self-check at end of each scene generation; Phase 5 acceptance test checks character description string match across scenes |
| Resume cache uses stale content after user edits input/bible/scene-plan | Step 6 hash-based cache invalidation: scene-NNN.md frontmatter stores SHA1(input + bible + plan + scene_row); mismatch → regenerate with WARN message |
| `{{args}}` flag parsing unreliable (LLM string match, not argv) | Step 0 explicit FLAG PARSE block with regex + echo-back; unknown flag halts with VN error |
| LLM regenerates whole bible (touches existing rows) | `append_bible_row.py` script (Phase 2) enforces append-only; bible-augmenter.md prompt instructs LLM to call script not rewrite |
| Scene-planner produces duplicate scenes near each other | Built-in uniqueness self-check + Phase 5 review |
| Genre detector misreads flashback chapter | Sample 3 chapters (first+middle+last) per R2 recommendation |
| Bible augmenter accidentally edits existing rows | Hard constraint + conflict log to `.work/bible-conflicts.md`; Phase 5 cross-file test verifies |
| Video prompt exceeds 8s (Veo3 hard limit) | Cap 3 beats × ~2.5s in `prompt-expander-video.md`; reject longer outputs in LLM self-check |
| Scene NNN cache stale after `--force-redo` race | `--force-redo` deletes ALL `.work/scene-*.md` upfront before loop starts |

## Security Considerations

- No secrets in prompt files
- `--series` flag writes to `~/.gemini/bibles/` (user-scoped, not system)
- Refusal logic for đam mỹ/ngôn tình enforced at TWO layers (genre-detector.md + references/genre-keywords.md BLOCKED row)

## Next Steps

- **Unlocks:** Phase 5 (end-to-end test with real files)
- **Verification needed:** Phase 5 long-file test + cross-file series test
