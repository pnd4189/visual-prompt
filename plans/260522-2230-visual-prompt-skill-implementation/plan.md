---
title: "Visual Prompt Skill Implementation"
description: "Antigravity CLI skill /visual-prompt — generate cinematic 4K image+video prompts from Vietnamese xianxia novels for YouTube audio videos"
status: implemented
priority: P1
branch: "main"
tags: [skill, antigravity, llm-driven, xianxia, prompts]
blockedBy: []
blocks: []
created: "2026-05-22T16:12:45.646Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt Skill Implementation

## Overview

Antigravity slash command `/visual-prompt <input.txt>` reads Vietnamese-proofread xianxia/wuxia novel files (8k-18k words, 1-2h audio) → emits `_image_prompts.txt` + `_video_prompts.txt` for copy-paste into Gemini/Qwen/ChatGPT (image) + Veo3/Seedance (video). Cross-file character bible persists series consistency. Pure LLM-driven (Gemini Ultra is loop driver); Python = minimal I/O helpers.

## Context Links

- **Brainstorm:** [brainstorm-260522-2230-visual-prompt-skill.md](../reports/brainstorm-260522-2230-visual-prompt-skill.md) — full design rationale
- **Research:**
  - [researcher-image-prompt-eng-260522.md](../reports/researcher-image-prompt-eng-260522.md) — image prompt eng 2025/2026
  - [researcher-video-prompt-eng-260522.md](../reports/researcher-video-prompt-eng-260522.md) — Veo3 official 5-part formula
- **Reuse codebase:** `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/` (scripts + patterns)

## Final Design Decisions (post-research)

| Item | Decision | Source |
|---|---|---|
| Image format | **Hybrid 200-300 words + sectioned** (Camera/Setting/Style/Lighting/Negative) | User confirmed 2026-05-22 (was 250-350 prose; revised per R1 + user choice) |
| Video format | **Google official 5-part:** Cinematography → Subject → Action(timestamped `[00:00-00:02.5]`) → Context → Style&Ambiance + Audio as scene layer | User confirmed 2026-05-22 (was Camera+Beats+AudioTag; revised per R2 Google Cloud doc) |
| Character consistency | **Identity Anchor verbatim** (paste exact text every scene) | R2 validated 8.5/10 vs 5-6/10 rewriting; R1 ref-image pattern DEFERRED (UX incompatible with copy-paste workflow) |
| Reference image pattern | **Deferred to v2** | Requires user to manually manage image files; current scope is text-only output |
| Cinema refs per genre | Crouching Tiger (2000), Hero (2002) for xianxia/wuxia | R1 + R2 both recommend |
| Camera section | Explicit in BOTH image+video prompts (shot type + lens + movement) | R1 + R2 both recommend |
| Per-genre negative lists | Universal anti-Western + xianxia-specific + style-specific | R1 recommended |
| Scene-tag → camera mapping | Add table to references/ | R2 contributed table |
| All other brainstorm decisions | **Unchanged** | See brainstorm doc |

## Phases

| Phase | Name | Status | Effort | Blocks |
|-------|------|--------|--------|--------|
| 1 | [Skeleton & Install](./phase-01-skeleton-install.md) | Done | ~1d | (none) |
| 2 | [Python I/O Scripts](./phase-02-python-i-o-scripts.md) | Done | ~0.75d | Phase 1 |
| 3 | [Reference Docs](./phase-03-reference-docs.md) | Done | ~1d | Phase 1 (parallel with 2) |
| 4 | [LLM Prompt Files](./phase-04-llm-prompt-files.md) | Done | ~1.5d | Phase 3 |
| 5 | [End-to-End Test](./phase-05-end-to-end-test.md) | Partial (script smoke ✓; LLM/Veo3 user-test) | ~1d | Phase 2 + 4 |
| 6 | [Docs & README](./phase-06-docs-readme.md) | Done | ~0.5d | Phase 5 |

**Total effort:** ~5.75 dev days (Phase 2 widened +0.25d for `append_bible_row.py` + assemble rewrite per red-team #1, #11). Phases 2 + 3 can run in parallel after Phase 1.

## Red-Team Review

Adversarial review completed 2026-05-22: [red-team-260522-2230-visual-prompt.md](../reports/red-team-260522-2230-visual-prompt.md) — 25 findings (5 critical). Applied fixes in-plan:

| Red-team finding | Fix location |
|---|---|
| #1 assemble_outputs.py is rewrite not adapt | Phase 2 (clarified scope + 150 LOC budget) |
| #2 Resume cache invalidation missing | Phase 4 (SHA1 hash in scene-NNN.md frontmatter) |
| #3 Image/video scene index collision | Phase 4 (unified scene-NNN.md with `has_video` flag) + Phase 2 (assemble preserves original indices) |
| #4 Wall-time budgets unrealistic | Phase 5 (widened to 5/25/50 min; batching deferred to triage if exceeded) |
| #5 Flag parsing unreliable | Phase 4 (Step 0 explicit FLAG PARSE block with regex + echo) |
| #6 Anchor enforcement | Phase 4 (mandatory char-for-char self-check in prompt-expander-image.md) |
| #11 Bible byte-identity drift | Phase 2 (`append_bible_row.py` helper) + Phase 4 (augmenter calls script not rewrite) |
| #14 Context overflow on long files | Phase 4 (chapter-excerpt-only load rule per scene) |

Remaining open questions surfaced to user (see "Unresolved" below).

## Dependencies

- **External:** Python 3.10+, `python-docx` (optional for .docx input), Antigravity CLI installed, Gemini Ultra active
- **Codebase reuse:** 3 scripts copied verbatim from `chinese-novel-proofreader/scripts/` (load_input.py, _io_utils.py, assemble_outputs.py — adapted)
- **No cross-plan dependencies** (greenfield, standalone)

## Architecture Summary

```
/visual-prompt <input.txt> [--series <name>] [--genre <name>] [--images N] [--videos M] [--force-redo]
   │
   ├─→ Step 1: load_input.py → JSON chapters
   ├─→ Step 2: Bible (LLM) — extract or augment {input_dir}/character-bible.md
   ├─→ Step 3: Genre detect (LLM, 2-3 chapters)
   ├─→ Step 4: Scene Plan Pass 1 (LLM, full file → .work/scene-plan.md)
   ├─→ Step 5: Expand Pass 2 (LLM, per scene → .work/scene-NNN.md, resume cache)
   └─→ Step 6: assemble_outputs.py → _image_prompts.txt + _video_prompts.txt
```

## Quality Bar (post-implementation acceptance)

See brainstorm §9. Additional post-research criteria:
- [ ] Image prompts 200-300 words sectioned (penalty if >320)
- [ ] Video prompts follow Google 5-part formula with ms-precision timestamps
- [ ] Audio cue embedded as scene layer (not appended tag)
- [ ] Each xianxia/wuxia prompt references Crouching Tiger or Hero
- [ ] Negative list per prompt = universal + genre-specific + style-specific (3 layers)

## Risks Carryover from Brainstorm

| Risk | Mitigation Phase |
|---|---|
| Genre detect sai (flashback chapter) | Phase 4 — read 2-3 chapters, not 1 |
| Bible drift cross-file | Phase 4 — bible-augmenter.md preserves existing rows |
| LLM lặp scene gần nhau | Phase 4 — scene-planner.md uniqueness self-check |
| Veo3 prompt truncation | Phase 3 — cap 800 words, 3 beats max |
| Antigravity install fragile on Windows | Phase 1 — setup.bat with copy fallback |

## User Decisions (recorded 2026-05-22)

1. **Antigravity install path** — VERIFIED against `/cli-tran` working skill on this machine. Pattern:
   - `~/.gemini/extensions/<skill>/` (extension layout — gemini-extension.json + commands/ + skills/)
   - `~/.gemini/commands/<skill>.toml` (slash command symlink)
   - `~/.gemini/antigravity-cli/plugins/<skill>/plugin.json` (Antigravity CLI plugin registry)
   - Phase 1 updated with verified paths.
2. **Veo3 timestamp syntax** — trust Google Oct 2025 doc, no extra manual verify. Fix in Phase 5 if test fails.
3. **Test fixtures** — synthesize 3 short xianxia samples (~1k words each) via LLM in Phase 5; medium/long = short × N concatenation. Avoids copyright concerns in test logs.

## Post-Implementation

- Run `/ck:cook /home/dung/VIBE_CODING/1. OTHERS/visual-prompt/plans/260522-2230-visual-prompt-skill-implementation/plan.md` to execute
- After ship: `/ck:journal` entry + add to portfolio
