---
phase: 5
title: Validation and Documentation
status: completed
priority: P2
effort: 3-4h
dependencies:
  - 1
  - 2
  - 3
  - 4
---

# Phase 5: Validation and Documentation

## Context Links

- Code: `docs/sample/qa-fixture.txt`
- Code: `part1_image_prompts.txt`, `part1_video_prompts.txt` as current low-detail examples
- Code: `README.md`, `HUONG-DAN-SU-DUNG.md`, `SKILL.md`
- Code: `scripts/calc_scene_count.py`

## Overview

Verify the count behavior, static safety language, and documentation. This phase
should not require a full paid/long Agy run to validate every prompt, but it must
give enough checks to catch regressions before manual production use.

## Requirements

- Functional: related tests/smoke commands prove count behavior.
- Functional: static grep catches unsafe style/likeness instructions.
- Functional: docs state Agy CLI target, high-count defaults, and runtime cost.
- Functional: docs explain the richer prompt structure and override flags.
- Non-functional: no full suite unless user asks; avoid committing generated large outputs unless explicitly approved.

## Architecture

Validation layers:

1. Script-level count tests/smoke commands.
2. Static prompt-contract grep.
3. Fixture or dry-run review of generated scene plan/prompt samples if feasible.
4. Documentation review.

Recommended static checks:

```bash
python3 scripts/calc_scene_count.py --input docs/sample/qa-fixture.txt
python3 scripts/calc_scene_count.py --input docs/sample/qa-fixture.txt --images 30 --videos 4
rg -n "in the style of|WLOP|Genshin|Crouching Tiger|celebrity|famous face|copy.*image" prompts references commands SKILL.md README.md HUONG-DAN-SU-DUNG.md
```

The grep should be interpreted carefully: banned phrases may appear in historical
plan reports, but not in active prompt/command/reference files unless they are
inside a "do not use" safety rule.

## Related Code Files

- Modify: `README.md`
- Modify: `HUONG-DAN-SU-DUNG.md`
- Modify: `SKILL.md`
- Modify: `docs/journals/*` only if the repo convention requires a session note
- Create: no large output artifacts by default
- Delete: none

## Implementation Steps

1. Run count smoke commands before and after Phase 1 changes.
2. Add or run a tiny focused test if the project has a test pattern; otherwise document exact smoke commands.
3. Run static grep for unsafe prompt-copying language.
4. Review active prompt/reference files manually for Agy wording and deep quality gates.
5. Update README and Vietnamese guide examples: default is 120-150 images + 20+ videos.
6. Mention longer runtime and recommend `--images/--videos` overrides for quick experiments.
7. Do not overwrite current `part*_image_prompts.txt` examples unless user asks; they look like manual artifacts.

## Success Criteria

- [ ] Count smoke commands pass.
- [ ] Override smoke commands pass.
- [ ] Static grep has no unsafe generated-prompt directives in active files.
- [ ] Docs say Agy CLI, not Gemini CLI runtime.
- [ ] Docs preserve four output files.
- [ ] User-facing guide clearly warns high-count runs take longer.

## Risk Assessment

- Risk: no automated LLM-level test can prove prompt quality.
  Mitigation: active prompt files contain explicit self-checks; manual sample review remains required.
- Risk: grep flags allowed safety examples.
  Mitigation: review hits by context; only generated positive directives are blockers.
- Risk: existing sample outputs remain low-detail and confuse users.
  Mitigation: either label them historical/manual or regenerate later by explicit user request.
