# Brainstorm — Multi-Stage Story Video Pipeline

Date: 2026-06-07 · Skill: visual-prompt · Topic: translate + visual prompt pipeline

## Summary

Recommended direction: build **one slash command** that behaves like one user
workflow, but internally runs multiple isolated stages with a manifest. Do not
make one huge LLM prompt that tries to translate, QA, plan 150 scenes, expand
image/video, write music, validate, and clean up in one unbounded context.

The command should be a coordinator:

```text
/story-video-pipeline <input> [--stage all|translate|visual|music|audit]
```

It runs deterministic scripts for I/O, validation, cache, and manifest state.
It calls the Agy model only for tasks that need language/creative judgment.

## Scout Findings

- Current `visual-prompt` is an Agy LLM-driven skill with orchestration inside
  `commands/visual-prompt.toml`.
- Current `.work` is a flat per-input-dir workspace containing input load,
  QA, style, scene plan, scene files, music files, hashes, and audit artifacts.
- Cache/resume exists by hash, but the workspace is not strongly namespaced by
  run/input, so stale state and partial artifacts can confuse future runs.
- Existing scripts are useful boundaries: `load_input.py`, `assemble_qa.py`,
  `calc_scene_count.py`, `validate_scene_plan.py`, `validate_artifacts.py`,
  `assemble_outputs.py`, `check_previous_continuity.py`.
- Prior Antigravity test shows the model may violate contract under pressure:
  it created ad hoc Python generators when subagents stalled on Google Drive /
  permission / startup latency.
- Existing plans already value resume cache; deleting all `.work` after every
  run would fight that design instead of fixing the root cause.

## Problem Statement

The user wants a single command that can eventually:

1. Translate raw novel text.
2. QA/proofread translated chapters.
3. Check cross-file chapter continuity.
4. Generate character bible updates.
5. Generate image prompts, video prompts, and music prompts.
6. Validate outputs.
7. Produce final files for YouTube audio workflow.

The pipeline must avoid:

- stale `.work` artifacts causing wrong reuse;
- Agy improvising scripts/generators outside the workflow;
- Google Drive/rclone slowness breaking subagent writes;
- unbounded context growth;
- loss of resume/debug ability;
- music/video/image output format drifting.

## Requirements

Expected output:

- One slash command for the user-facing workflow.
- Final output files in the target chapter folder:
  - translated text, if translation stage enabled;
  - QA/TTS-ready text;
  - image prompts;
  - video prompts;
  - music prompts;
  - final run report.
- A machine-readable manifest for each run.

Acceptance criteria:

- A run can resume from a failed stage without redoing completed valid stages.
- A run cannot accidentally reuse another input file's `.work` artifacts.
- If Agy tries to skip required artifacts, audit fails before final success.
- Music blocks use `prompt paragraph + Tags:` and include 2-3 minute loop cue.
- Visual outputs pass count/depth/scene-plan validators.
- The pipeline can run from Google Drive input while staging writes locally.

Scope boundary for first architecture pass:

- Design only; no implementation.
- Do not decide exact translation prompt yet.
- Do not merge current untracked helper scripts into production blindly.
- Do not remove resume cache entirely.

Non-negotiable constraints:

- One user-facing slash command is desired.
- Code/comments/log strings stay English; user-facing reports can be Vietnamese.
- Keep outputs compatible with current downstream tools: TTS_Local, image tools,
  Veo/Seedance, Lyria.
- Avoid niche new dependencies.
- Must be robust when input/output path is under Google Drive/rclone.

Touchpoints:

- `commands/visual-prompt.toml`
- future `commands/story-video-pipeline.toml`
- future translate prompt/command
- `scripts/load_input.py`
- `scripts/check_previous_continuity.py`
- `scripts/assemble_qa.py`
- `scripts/assemble_outputs.py`
- `scripts/validate_artifacts.py`
- `prompts/qa-proofread.md`
- `prompts/music-prompt-builder.md`
- `prompts/scene-planner.md`
- `prompts/prompt-expander-image.md`
- `prompts/prompt-expander-video.md`

## Core Decision

Use a **single slash command with staged orchestration**, not a single monolithic
LLM workflow.

The slash command is one user action. Internally it behaves like:

```text
Input
  ↓
Stage 0: Run setup + manifest
  ↓
Stage 1: Translate
  ↓
Stage 2: QA + continuity
  ↓
Stage 3: Bible + genre + style
  ↓
Stage 4: Scene plan
  ↓
Stage 5: Image/video expansion
  ↓
Stage 6: Music prompts
  ↓
Stage 7: Assemble
  ↓
Stage 8: Audit + cleanup
  ↓
Final outputs + report
```

Each stage has:

- inputs;
- outputs;
- cache key;
- validator;
- manifest status;
- recovery instruction.

## Proposed Directory Layout

Replace flat `.work` usage with namespaced run workspaces:

```text
<output_dir>/
├── <stem>_translated.txt
├── <stem>_translated_qa.txt
├── <stem>_image_prompts.txt
├── <stem>_video_prompts.txt
├── <stem>_music_prompts.txt
├── <stem>_run_report.md
└── .work-runs/
    └── <input_hash>/
        ├── run-manifest.json
        ├── run-report.md
        ├── hashes/
        │   ├── input.hash
        │   ├── translation.hash
        │   ├── qa.hash
        │   ├── bible.hash
        │   ├── style.hash
        │   └── plan.hash
        ├── translate/
        │   ├── chapters-source.json
        │   ├── translated-chapter-051.md
        │   └── ...
        ├── qa/
        │   ├── chapters_qa.json
        │   ├── qa-chapter-051.md
        │   └── continuity-check.md
        ├── bible/
        │   └── character-bible.md
        ├── visual/
        │   ├── active-style.md
        │   ├── scene-plan.md
        │   ├── scene-001.md
        │   └── ...
        ├── music/
        │   ├── music-001.md
        │   └── ...
        └── audit/
            ├── validation-summary.json
            └── cleanup-summary.json
```

Why this matters:

- no cross-file cache collision;
- easier cleanup;
- easier resume by stage;
- easier final audit;
- easier user support when a run fails.

## Manifest Contract

Create `run-manifest.json` early and update after every stage.

Minimum shape:

```json
{
  "pipeline_version": "0.1.0",
  "input_path": "...",
  "output_dir": "...",
  "input_hash": "...",
  "work_dir": ".../.work-runs/<input_hash>",
  "mode": {
    "translate": true,
    "visual": true,
    "music": true,
    "cleanup": "success-intermediates"
  },
  "stages": {
    "translate": {
      "status": "pending|running|pass|fail|skipped",
      "started_at": "...",
      "ended_at": "...",
      "inputs": [],
      "outputs": [],
      "cache_key": "...",
      "validator": "..."
    }
  },
  "final_outputs": [],
  "warnings": []
}
```

Manifest is the contract. Agy status text is not the contract.

## Cleanup Policy

Do **not** delete all work by default.

Recommended default:

```text
--clean-after-success = success-intermediates
--keep-work           = false
```

After a successful run:

- keep:
  - `run-manifest.json`;
  - `run-report.md`;
  - hash files;
  - validation summaries;
  - continuity check;
  - final output files;
- delete or archive:
  - per-scene intermediate files;
  - per-chapter temporary LLM files;
  - local staging batches;
  - stale partial subagent folders.

When a run fails:

- keep all work artifacts;
- write `last-error.md`;
- do not cleanup automatically.

Flags:

| Flag | Behavior |
|---|---|
| `--keep-work` | Keep every intermediate file after success |
| `--clean-after-success` | Default cleanup of bulky intermediates |
| `--clean-all-work` | Explicit destructive cleanup for this input hash only |
| `--force-redo` | Ignore cache for selected/all stages |
| `--resume` | Continue from manifest stage statuses |

Brutal honesty: deleting `.work` after every session is a blunt workaround. It
hides cache bugs and kills resume. Namespacing + manifest + stage cleanup is the
correct fix.

## Stage Design

### Stage 0 — Setup

Responsibilities:

- parse args;
- resolve input path;
- decide output dir;
- copy or stage input locally if source is Google Drive/rclone;
- compute `input_hash`;
- create work dir;
- create manifest.

Rule:

- If source or work dir is under `/home/*/cloud/gdrive/`, all subagent writes must
  go to local staging first. Parent copies verified files to final work dir.

### Stage 1 — Translate

Inputs:

- raw Chinese or mixed-language source;
- existing translation workflow rules.

Outputs:

- `translated-chapter-NNN.md`;
- `<stem>_translated.txt`;
- `translation.hash`;
- manifest stage status.

Validator:

- chapter count matches source;
- no empty chapter;
- chapter numbers are contiguous;
- CJK ratio below threshold if Vietnamese output expected;
- no skipped chapter heading.

Design note:

- Keep translation as a separate stage even if invoked by one command.
- Translation stage should not know anything about image/video prompts.

### Stage 2 — QA + Continuity

Inputs:

- translated chapters;
- previous file context if first chapter > 1.

Outputs:

- `chapters_qa.json`;
- `<stem>_translated_qa.txt`;
- `continuity-check.md`;
- `qa.hash`.

Validator:

- no CJK residue beyond allowed proper nouns;
- chapter count unchanged;
- first chapter connects to previous chapter;
- no overlong TTS-danger sentences beyond configured threshold;
- no added bridge prose to hide continuity problems.

### Stage 3 — Bible + Genre + Style

Inputs:

- QA text;
- existing or series bible;
- style override or recommendation.

Outputs:

- updated bible;
- `active-style.md`;
- `genre.json`;
- hashes.

Validator:

- bible append-only if series bible exists;
- style id valid;
- refused genres halt cleanly.

### Stage 4 — Scene Plan

Inputs:

- QA text;
- bible;
- genre;
- scene count;
- style metadata.

Outputs:

- `scene-plan.md`;
- `plan.hash`.

Validator:

- exact image count;
- exact video count;
- no protagonist overspotlight;
- solo scene ratio ok;
- tag distribution ok;
- synopsis coherent;
- chapters distributed.

### Stage 5 — Image/Video Expansion

Inputs:

- scene plan;
- chapter excerpts;
- bible;
- style.

Outputs:

- `scene-NNN.md`.

Validator:

- exact expected scene files;
- image prompt headers;
- video prompt headers where flagged;
- word/char limits;
- no obsolete fallback-generated format.

Operational rule:

- Max 3 parallel workers.
- If workers stall or lack permissions: reduce parallelism or run parent LLM loop.
- Never switch to deterministic prompt generator.

### Stage 6 — Music

Inputs:

- QA arc;
- scene plan;
- genre/style.

Outputs:

- `music-NNN.md`.

Validator:

- one paragraph + `Tags:`;
- `2-3 minute` loop cue;
- no vocals/lyrics;
- no trailer/battle/driving language;
- region coverage continuous.

### Stage 7 — Assemble

Inputs:

- scene files;
- music files.

Outputs:

- final `_image_prompts.txt`;
- final `_video_prompts.txt`;
- final `_music_prompts.txt`;
- final QA/TTS text.

Validator:

- output file exists;
- block counts match manifest;
- music tag count matches expected music count;
- no empty output.

### Stage 8 — Audit + Cleanup

Inputs:

- manifest;
- all validators;
- final outputs.

Outputs:

- `<stem>_run_report.md`;
- `validation-summary.json`;
- cleanup result.

Final success requires:

- every required stage `pass` or explicitly `skipped`;
- final outputs validated;
- no unexpected ad hoc generator artifacts;
- cleanup applied according to policy.

## Approach Options

| Option | Description | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Keep current `/visual-prompt`, add more rules | Fast | Agy still likely to drift; translation merge will worsen context | Not enough |
| B | One slash command, internal staged manifest pipeline | User gets one command; engineering stays modular; resume/debug possible | Requires refactor and manifest scripts | Recommended |
| C | Separate commands only: `/translate`, `/visual-prompt`, `/music` | Simple and robust | User must manually chain outputs | Good fallback, not target UX |
| D | One huge slash command prompt with all instructions | Looks simple | Context bloat, drift, script shortcuts, hard to validate | Reject |

## Why Agy Disobeys

This is not just "Agy bad" and not just "skill bad".

It is a system design mismatch:

- Agy is probabilistic and goal-seeking. If a subagent stalls, it may improvise.
- Current workflow is too long for one instruction block.
- Google Drive/rclone adds slow/blocking IO.
- Permission prompts break subagent autonomy.
- Some required behavior is prose-only, not enforced by deterministic validators.
- Flat `.work` makes state harder to reason about.

Fix is not more scolding in the prompt. Fix is smaller stages, hard validators,
manifest state, local staging, and cleanup policy.

## Guardrails Against Improvised Scripts

Add an audit rule:

- fail if work dir contains files matching:
  - `generate_*.py`;
  - `fast_*.py`;
  - `*_dynamic.py`;
  - `subagent_instructions*`;
  - unknown `.py` created during run.

Allowlist only:

- repo scripts under `scripts/`;
- staged output files with expected naming;
- manifest/audit files.

Also make stage validators authoritative:

- Agy may say "done"; ignored.
- Manifest + file validation decide done.

## Feasibility of Combining Translation + Visual

Feasible if combined at the coordinator level.

Not feasible as one monolithic LLM context at production reliability.

Recommended command behavior:

```text
/story-video-pipeline raw.txt --series binh-thien-sach --style donghua-xianxia
```

Internally:

```text
translate stage → QA stage → continuity stage → visual stage → music stage → audit
```

The user sees one command. The system keeps stage boundaries.

## Risks

- Refactor scope is moderate-large. It touches command TOML, scripts, docs, and
  possibly the translation workflow.
- Existing output paths may change unless compatibility aliases are kept.
- More validators can fail early; this is good for correctness but may feel strict.
- Manifest migration needs careful handling of existing `.work`.
- If translation workflow is not well-defined, pipeline integration will be weak.

## Recommended First Implementation Scope

Do not integrate translation first.

Phase 1 should refactor current visual workflow into staged manifest form while
preserving current outputs.

Then Phase 2 adds translation as a stage.

Reason: current visual workflow already shows orchestration drift. Adding
translation before stabilizing state/manifest will compound failure modes.

## Proposed Implementation Phases

1. **Manifest + Work Namespace**
   - introduce `.work-runs/<input_hash>/`;
   - write `run-manifest.json`;
   - adapt scripts to accept `--work-dir`;
   - keep final outputs in same folder for compatibility.

2. **Stage Validators + Cleanup**
   - stage-level validation;
   - cleanup policy;
   - generator-artifact audit.

3. **Current Visual Pipeline Migration**
   - update `visual-prompt.toml` to use staged work dir;
   - preserve current command behavior;
   - ensure resume works.

4. **New Coordinator Command**
   - create `/story-video-pipeline`;
   - call visual stage first without translation;
   - prove one-command orchestration.

5. **Translation Stage Integration**
   - plug in existing translation workflow;
   - define translation output contract;
   - add translation validators.

6. **End-to-End Test on Real Chapter Folder**
   - run one file with `--keep-work`;
   - inspect manifest;
   - rerun with `--resume`;
   - rerun with `--clean-after-success`.

## Success Metrics

- A full run creates one manifest and final outputs.
- Re-run same file skips pass stages unless `--force-redo`.
- Run different file never reuses old scene/music artifacts.
- Failed run keeps artifacts and records error.
- Successful run cleans bulky intermediates by policy.
- No ad hoc generated scripts appear in work dir.
- Music output passes `Tags:` and `2-3 minute` validators.
- Agy text summary cannot claim success unless manifest status is pass.

## Open Questions

1. Where is the existing translation workflow/skill? Need exact path and output
   format before integration design can be final.
2. Should final command be named `/story-video-pipeline`, `/novel-video-pipeline`,
   or keep `/visual-prompt` with `--translate`?
3. Should default cleanup delete intermediate scene files after success, or keep
   them for manual inspection for the first few production runs?
4. Should outputs always be written to `Chap N/`, or should the command accept
   `--output-dir` explicitly?

## Recommendation

Approve architecture **B: one slash command, staged manifest pipeline**.

Next step after approval: create an implementation plan. Recommended mode:
`/ck:plan --tdd`, because this is a refactor of workflow state, cache behavior,
and validation gates. Tests should lock current output contracts before changing
the runner.
