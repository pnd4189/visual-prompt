# Red Team Report

## Summary

The plan is feasible, but three risks can break implementation quality:
scene repetition, unsafe style anchor residue, and prompt bloat. The phase files
include mitigations for all three.

## Findings

### 1. 120-150 prompts can amplify repetition

Risk: a short chapter file cannot naturally support 150 distinct named moments.

Mitigation in plan:
- Phase 3 requires micro-moment splitting, category mix, map shots, group scenes,
  and stricter duplicate checks.
- No hallucinated named characters; supporting crowds can stay generic.

### 2. Removing named IP/artist anchors can weaken style control

Risk: generic "cinematic fantasy" may drift.

Mitigation in plan:
- Phase 2 replaces anchors with concrete visual descriptors: medium, palette,
  line/render style, lighting, material, camera language.
- Style ids remain stable.

### 3. Deep prompts can become filler-heavy

Risk: longer prompt target produces word salad and worse output.

Mitigation in plan:
- Phase 2 and 4 require concrete scene facts, not generic quality modifiers.
- Self-check rejects shallow or filler prompts.

### 4. Parser compatibility risk

Risk: adding new headers might break assembly.

Mitigation in plan:
- Phase 4 keeps existing video headers.
- `assemble_outputs.py` extracts full body under `## Image Prompt`, so richer image sections are safe.

### 5. Agy vs `.gemini` path ambiguity

Risk: docs/runtime wording changes to Agy, but install/bible paths may still use `.gemini`.

Mitigation in plan:
- Phase 1 only changes runtime wording unless install behavior is verified.
- Scout report leaves path verification as implementation note.

## Status

DONE_WITH_CONCERNS: plan is ready, but implementation must be strict about not editing historical reports and not regenerating large sample outputs without user approval.
