# Researcher Report: Prompt Depth and Count Policy

## Summary

The current pipeline can scale to high prompt counts without new architecture:
count policy is isolated in `scripts/calc_scene_count.py`, and the LLM expands
scene rows independently. The real risk is repetition, not scripting complexity.

## Findings

- Default counts should be centralized in `compute()` only.
- User wants "mỗi lần" around 120-150 images, so default should clamp to that band.
- `--images` and `--videos` are user decisions and should not be clamped.
- High prompt count requires scene diversity rules before expansion; otherwise output becomes 120 variants of solo portraits.
- Current sample outputs (`part1_image_prompts.txt`) are much shorter than the current spec, so command/prompt instructions need harder self-check language.

## Recommended Count Formula

```python
auto_images = min(150, max(120, round(wordcount / 120)))
auto_videos = max(20, round(auto_images / 6))
```

Behavior:
- 2k-14k words mostly produce 120 images.
- 18k words produce 150 images.
- default video count becomes 20-25.
- overrides remain exact.

## Prompt Depth Translation From Bình Thiên Sách Template

Reusable structural elements:
- Metadata/story DNA.
- Character/weapon/power locks.
- Multi-layer background.
- Color DNA and shadow rules.
- Composition hierarchy.
- Output and self-check requirements.

Do not hardwire Bình Thiên Sách content into every story. Use it as the quality
standard and sectioning model.

## Risks

- Higher counts multiply runtime and cost.
- Short source files may need many micro-scenes; planner must split by beats,
  environment, groups, ritual/action moments, and map-scale transitions.

## Recommendations

- Update scene planner before relying on new counts.
- Add explicit "shallow prompt rejection" checks.
- Keep parser-compatible headers where possible.
