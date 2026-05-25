---
phase: 3
title: "Reference Docs"
status: done
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 3: Reference Docs

## Overview

Static knowledge base the LLM loads on-demand during workflow execution. These files encode the design decisions (image/video format spec, genre vocab, character bible rules, YouTube pacing, scene-tag camera mapping, negative lists). Phase 4 prompt files reference these via `@references/<name>.md` syntax. Can run parallel with Phase 2.

## Context Links

- Brainstorm §4 (knowledge files), §8 (post-research enhancements)
- Research R1: image prompt engineering (200-300 word sectioned format, cinema refs, negatives)
- Research R2: video prompt engineering (Google 5-part formula, scene-tag → camera mapping table, audio as scene layer, character bible verbatim 8.5/10)
- Reference template: `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/references/visual-prompt-template.md` (copy + enhance)

## Requirements

**Functional:**
- LLM can produce on-spec image prompts (hybrid 200-300 word sectioned) and video prompts (Google 5-part formula with ms-timestamps) by reading only these references + the input chapter
- Genre detection has unambiguous VN↔EN keyword tables
- Character bible enforces verbatim Identity Anchor rule with examples
- YouTube pacing guide answers "how many images + videos per 1h/2h audio" with rationale
- Scene-tag → camera mapping table covers all 7 scene tags (establishing, action, dialogue, reveal, emotional, ritual, travel)
- Per-genre negative lists prevent Western-fantasy drift + style-specific artifacts

**Non-functional:**
- Each reference file <300 lines (LLM context budget per @reference load)
- All content in English (LLM works best with English instructions); VN keywords listed in tables for input matching
- Examples are concrete (real prompts, not placeholders)

## Architecture

```
references/
├── visual-prompt-template.md       # MASTER format spec — image (sectioned 200-300w) + video (5-part) with full examples
├── genre-keywords.md               # VN↔EN vocab tables for tiên hiệp/huyền huyễn/đô thị/cổ điển/võ hiệp/đam mỹ-block
├── identity-anchor-rules.md        # Character bible structure + verbatim usage rule + examples
├── youtube-pacing-guide.md         # Image/video count formulas + scene placement rhythm for 1h/2h audio
├── scene-tag-camera-mapping.md     # 7 scene tags → shot type/lens/movement table (from R2)
└── negative-lists.md               # Universal anti-Western + genre-specific + style-specific negatives
```

## Related Code Files

### Create
- `references/visual-prompt-template.md` — copied from proofreader template, REWRITTEN sections:
  - Image format: hybrid 200-300 word sectioned (Camera / Setting / Subject / Style / Lighting / Negative)
  - Video format: Google 5-part (Cinematography → Subject → Action [timestamped `[00:00-00:02.5]`] → Context → Style & Ambiance), Audio as scene layer in Style & Ambiance
  - 1 full worked example per format (xianxia scene)
  - Per-platform tweaks block (Gemini/Qwen/ChatGPT/Veo3/Seedance) retained
- `references/genre-keywords.md` — 6 genre tables (tiên hiệp, huyền huyễn, đô thị, cổ điển, võ hiệp, đam mỹ-block). Each: 8-12 VN trigger words → EN visual translation. Example row: `tu tiên → cultivation, lotus seat meditation, qi flowing through dantian`
- `references/identity-anchor-rules.md` — sections: (1) bible YAML row schema, (2) Identity Anchor mandatory fields (age, build, hair, face, signature mark, attire base), (3) verbatim rule with WHY (R2 8.5/10 vs 5-6/10), (4) bad/good examples, (5) augmentation rule (new char → append row, never delete)
- `references/youtube-pacing-guide.md` — sections: (1) formula `images = round(wc/200)`, `videos = round(images/7)`, (2) rationale: YouTube algorithm penalizes >8s static frames; visual cuts every 6-8s, (3) tables: 1h audio (~9k words) = ~45 images + 6 videos; 2h audio (~18k words) = ~90 images + 13 videos, (4) scene placement rhythm: openers (1 video), climax (1 video), dialogue dense → more images, action dense → more videos
- `references/scene-tag-camera-mapping.md` — table from R2 + brainstorm: 7 tags × 4 cols (Scene Tag | Shot Type | Lens (mm) | Camera Movement). Example: `action → Medium-wide tracking | 35mm | Handheld follow with motion blur`
- `references/negative-lists.md` — 3 sections: (1) Universal anti-Western (medieval armor, dragons-with-wings, gothic cathedral, blonde hair, blue eyes default — 10 items), (2) Genre-specific (xianxia: no jeans/sneakers, no glasses, no neon | võ hiệp: no magic explosions | đô thị: no cultivation robes), (3) Style-specific (no logo/watermark/text overlay/distorted hands/extra fingers — universal AI gen issues)

### Modify
- (none)

### Delete
- (none)

## Implementation Steps

1. **Open proofreader's `visual-prompt-template.md`** and identify sections to KEEP vs REWRITE:
   - KEEP: Genre Keywords VN↔EN (move to `genre-keywords.md`), 7 Scene Tags concept (move to `scene-tag-camera-mapping.md`), Per-Platform Tweaks, Anti-Drift Guard List (move to `negative-lists.md`)
   - REWRITE: Image format section (was prose 250-350w → sectioned 200-300w), Video format section (was Camera+Beats+AudioTag → Google 5-part with ms-timestamps + audio as scene layer)
2. **Write `visual-prompt-template.md`** — master format spec with 2 full worked examples (1 image, 1 video) for a xianxia sword duel scene; cite Crouching Tiger anchor; show exact section headers LLM must use
3. **Write `genre-keywords.md`** — 6 tables, ~10 rows each; tiên hiệp/huyền huyễn most detailed (primary use case); đam mỹ row = `BLOCKED — skill refuses with explanation`
4. **Write `identity-anchor-rules.md`** — frame WHY first (R2 empirical 8.5/10), then schema, then 1 bad example (rewriting each scene) and 1 good example (verbatim Identity Anchor block pasted into every prompt's Subject section)
5. **Write `youtube-pacing-guide.md`** — start with formula, then 2 worked tables (1h/2h), then rationale paragraph citing YouTube algorithmic penalty for static frames
6. **Write `scene-tag-camera-mapping.md`** — single table from R2; add 1-line "when to use" hint per tag
7. **Write `negative-lists.md`** — 3 lists; each item is a single phrase the LLM appends to negative prompt section
8. **Cross-link references** — at top of each file, add "Related: [[other-ref-name]]" note (e.g., `visual-prompt-template.md` links to all 5 others)
9. **Audit total line count** — sum should be ~1200-1500 lines across 6 files; trim verbose paragraphs

## Todo List

- [ ] `references/visual-prompt-template.md` written with 2 worked examples + correct format spec
- [ ] `references/genre-keywords.md` written (6 genre tables, đam mỹ blocked)
- [ ] `references/identity-anchor-rules.md` written (verbatim rule + WHY + examples)
- [ ] `references/youtube-pacing-guide.md` written (formula + 1h/2h tables + rationale)
- [ ] `references/scene-tag-camera-mapping.md` written (7 tags × shot/lens/movement)
- [ ] `references/negative-lists.md` written (3 layers: universal + genre + style)
- [ ] Cross-links added at top of each file
- [ ] Total line count ≤1500 across 6 files

## Success Criteria

- [ ] Each reference file <300 lines
- [ ] `visual-prompt-template.md` has 1 image + 1 video worked example, each clearly labeled "EXAMPLE — DO NOT COPY VERBATIM, ADAPT TO SCENE"
- [ ] `genre-keywords.md` covers all 5 supported genres + 1 blocked
- [ ] `scene-tag-camera-mapping.md` covers all 7 scene tags from brainstorm §3.2
- [ ] `negative-lists.md` has exactly 3 sections (universal/genre/style)
- [ ] Identity Anchor example in `identity-anchor-rules.md` is paste-able verbatim into a Subject section

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Reference files exceed LLM context budget when all loaded | Cap each <300 lines; Phase 4 prompts load only relevant refs per step (not all 6 at once) |
| Genre keyword table misses a sub-genre (e.g., wuxia vs xianxia confusion) | Cross-reference brainstorm §3.1; user review pass before Phase 4 |
| Worked examples leak as actual output (LLM copies verbatim) | "ADAPT TO SCENE — DO NOT COPY VERBATIM" warning labels on every example |
| Negative list bloat → token cost per prompt explodes | Cap 10 items universal + 5 genre + 5 style = 20 negatives max per prompt |
| Veo3 audio cue format changes (still beta) | Document Oct 2025 format with link; flag for re-verification before each major run |

## Security Considerations

- No secrets, no credentials in references
- đam mỹ/ngôn tình block enforced at reference level (genre-keywords.md returns BLOCKED) AND at Phase 4 prompt level (genre-detector.md refuses)

## Next Steps

- **Unlocks:** Phase 4 (LLM prompts `@reference` these files)
- **Verification needed:** Phase 5 end-to-end test confirms LLM output matches format spec
