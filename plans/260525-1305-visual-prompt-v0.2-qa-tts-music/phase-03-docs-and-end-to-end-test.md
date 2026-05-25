---
phase: 3
title: "Docs and End-to-End Test"
status: done
priority: P2
effort: "2-3h"
dependencies: [1, 2]
---

# Phase 3: Docs and End-to-End Test

## Overview

Update `SKILL.md` + `HUONG-DAN-SU-DUNG.md` to document the QA-first workflow, the
4-file output set, the TTS hand-off (VieNeu/VietVoice), and the Lyria music-prompt
usage + limitations. Then run a real end-to-end pass on a small sample novel to
verify the full chain (QA → bible → genre → scenes → music → assemble) produces all
4 files correctly.

## Requirements

- **Functional**
  - `SKILL.md`: workflow now 8 steps (QA-first), output spec lists 4 files, drop the
    "input must be pre-proofread" assumption (skill self-QAs), add `--music` to usage.
  - `HUONG-DAN-SU-DUNG.md`: new QA step section; how to feed `<stem>_qa.txt` into
    TTS_Local (`python tts_cli.py <stem>_qa.txt --engine vieneu|vietvoice --voice ...`);
    how to paste `<stem>_music_prompts.txt` blocks into Lyria 3 (Gemini app); the
    "how many loops" guidance (3-5, default 4); Lyria limitations (no 100% vocal
    exclusion, manual timeline placement, clip length).
  - End-to-end run on a sample produces `_qa.txt`, `_image_prompts.txt`,
    `_video_prompts.txt`, `_music_prompts.txt` with no errors.
- **Non-functional**
  - Docs in the existing bilingual style (SKILL.md English, HUONG-DAN Vietnamese).
  - Do NOT reference plan phase numbers / finding codes in docs or code comments.

## Architecture

Documentation-only + verification. No new runtime components. The E2E test is a
manual/scripted invocation of `/visual-prompt` on a fixture novel (reuse or trim an
existing sample; if none, create a tiny 2-chapter VN fixture with deliberate
residual Chinese chars + one over-long sentence to exercise QA).

## Related Code Files

- Modify: `SKILL.md` — Philosophy (add QA gate), Workflow (8 steps), Usage
  (`--music N`), Output Spec (4 files), Limitations (Lyria vocal caveat).
- Modify: `HUONG-DAN-SU-DUNG.md` — QA step, TTS feed, Lyria paste, loop guidance.
- Create (test fixture, if needed): `docs/sample/qa-fixture.txt` — tiny VN novel
  with planted residual CJK + long sentence (for repeatable E2E).
- Verify only (no edit unless bug found): all Phase 1/2 created/modified files.

## Implementation Steps

1. Update `SKILL.md`: revise Philosophy, Workflow (insert STEP 1.5 + 6.5),
   Usage line (`--music N`), Output Spec (4 files), File Layout (new prompt +
   reference + script), Limitations (Lyria caveat + manual sync).
2. Update `HUONG-DAN-SU-DUNG.md`: add §QA (what it fixes, that it always runs),
   §TTS (exact `tts_cli.py` commands for both engines, note chapter titles are
   spoken), §Lyria (paste workflow, 3-5 loop guidance, instrumental-only caveat,
   manual placement by `Chương X-Y` label).
3. Prepare a small fixture (or trim an existing input) with planted residual
   Chinese chars + one >200-char sentence.
4. Run `/visual-prompt docs/sample/qa-fixture.txt --music 3` end-to-end.
5. Verify: 4 output files exist; `_qa.txt` has no residual CJK and chapter titles
   end with a period; `_music_prompts.txt` has 3 instrumental blocks with the
   negative line; image/video files still well-formed; cache works on re-run
   (no regeneration when unchanged; `--force-redo` regenerates).
6. Fix any defects found, re-run until clean.

## Success Criteria

- [ ] `SKILL.md` reflects 8-step QA-first workflow + 4 outputs + `--music` + Lyria
      limitation; no "must be pre-proofread" assumption left.
- [ ] `HUONG-DAN-SU-DUNG.md` has runnable TTS commands + Lyria paste guide + loop
      advice + caveats.
- [ ] E2E run yields all 4 files with no errors; `_qa.txt` CJK-free + titled with
      terminal periods; `_music_prompts.txt` instrumental-only with negatives.
- [ ] Re-run is cache-stable; `--force-redo` regenerates QA + scenes + music.
- [ ] No plan-artifact references in docs/code comments.

## Risk Assessment

- **No existing automated test harness** for these I/O scripts → E2E is manual.
  Mitigation: scripted fixture + explicit checklist above; keep fixture in repo for
  future runs.
- **Docs drift** from actual behavior if Phase 1/2 changed late. Mitigation: write
  docs AFTER Phase 1/2 land; verify each documented command against real output.
- **LLM run cost/time** for E2E on large input. Mitigation: use a tiny fixture, not
  a full 18k-word novel.
