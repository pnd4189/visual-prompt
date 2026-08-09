# Audit + fix: Agy active-model runtime guard

Range audited: `9c37715..e81daa8` · plan `260808-visual-prompt-active-model-runtime-guard` · journal `260809-1703-active-model-runtime-guard`
Verified live against Agy CLI 1.1.11 (`agy.real`, Gemini 3.1 Pro High) on 2026-08-09.

## Verdict

The Codex work is **structurally correct but was not armed on the path the user
actually uses**. Hook contract, tool names, payload shape, provenance logging and
the `.work` write scoping all match the real Agy runtime — verified by capturing
live hook payloads. But before this session's fix, a direct `/visual-prompt`
invocation ran with the guard **disabled**, and the fail-closed layer only ever
applied to `run-folder.sh` batch runs (`VP_GUARD_ACTIVE=1`).

## Evidence collected (live, not inferred)

Hook contract extracted from the embedded docs + proto descriptors inside
`agy.real`, then confirmed by dumping real payloads through the installed guard:

- Payload is flat camelCase (`conversationId`, `transcriptPath`,
  `artifactDirectoryPath`, `toolCall{name,args}`, `invocationNum`) — matches the guard.
- Real tool names confirmed: `write_to_file` (`TargetFile`/`CodeContent`),
  `list_dir`, `view_file`, `grep_search`, `run_command`.
- `PostToolUse` payload does carry `toolCall` → provenance logging works.
- `~/.gemini/config/hooks.json` (global install) fires; hook cwd is
  `~/.gemini/config`; each hook event fires **twice** per step.
- `_agy_launcher_cwd()` recovers the launch directory through the `agy` shim +
  `systemd-run` scope → write roots resolve even though print mode sends
  `workspacePaths: []`.

## Findings

| # | Sev | Finding |
|---|-----|---------|
| F1 | Critical | **Guard never armed on direct runs.** Agy records only the raw `/visual-prompt:visual-prompt …` user turn in `transcript_full.jsonl`; the expanded TOML prompt is never written there. `VISUAL_PROMPT_ACTIVE_MODEL_GUARD_V1` therefore entered the transcript only if the model chose to `view_file` the TOML — i.e. the guard was armed by the very diligence it was meant to enforce. A model that skips the contract (the exact 260805 flash-tier failure) got zero enforcement. |
| F2 | High | **Rules message never delivered.** `_pre_invocation` injected only at `invocationNum == 0`, but arming happened later (measured: first 6 hook calls inactive). Net effect: no guidance was ever injected. |
| F3 | High | **Unquoted absolute helper path was denied.** The skill root contains a space (`1. OTHERS`); `shlex` split it, so `python3 <root>/scripts/load_input.py` resolved to a bogus script name and every canonical helper was refused with an unhelpful reason. |
| F4 | High | **Mirrored installs were locked out.** `setup.bat` copies the whole skill when Windows denies symlinks, and Agy keeps its own plugin copy; helpers run from those prefixes failed the `SKILL_ROOT` identity check → pipeline bricked on those installs. |
| F5 | Medium | **Deny-by-default covered Agy's benign step types.** `READ_TOOLS` used Windsurf-era names; agy also emits `list_directory`, `view_file_outline`, `notify_user`, `memory`, `checkpoint`, … Any of them would have been denied mid-run. Never observed because the guard had never been armed in a full run. |
| F6 | Medium | **Plan phase-01 claim unproven.** Workspace `.agents/hooks.json` was not loaded in the observed run (agy logged `loaded 1 named hooks from 1 hooks.json file(s)` = the global one). Inconclusive for interactive mode, but the plan states it as done. |
| F7 | Low | **Stale plugin copy.** `~/.gemini/config/plugins/visual-prompt/` is a full copy of the repo from 2026-08-08 21:17 (only `scripts/` is symlinked). Its `commands/visual-prompt.toml` — which the model actually reads on direct runs — is one line behind the repo. Skill-contract edits do not reach it until the plugin is re-imported. |
| F8 | Low | Leftover `.agy-guard-smoke.oEqYDb/` directory inside the plugin copy — a snapshot of a smoke-test dir that existed in the skill root on 2026-08-08. The repo root is clean now. |
| F9 | Info | Batch harness swapped `--dangerously-skip-permissions` → `--sandbox` and added `--agent visual-prompt-writer`. No batch run has been executed since; approval-prompt behaviour under `--sandbox` is unverified. |

## Fixes applied

- `scripts/active_model_guard.py`
  - Arm from the user's invocation turn (`<USER_REQUEST> /visual-prompt…`) as well
    as the contract marker; scan head + tail of the transcript. Fixes F1.
  - `_claim_primary` now reports whether it created the state; the rules message
    is injected exactly once, on the first armed turn, and names the required
    `check_run_legit` authorship flags. Fixes F2.
- `scripts/active_model_command_policy.py`
  - Mask the literal skill root before `shlex` so unquoted absolute helper paths
    with spaces resolve correctly; denial reason now names the requirement. Fixes F3.
  - `_is_canonical_helper()` accepts a helper from any install prefix when its
    bytes are identical to the canonical file, and rejects any edited or invented
    script. Fixes F4 without weakening the allowlist.
- `scripts/active_model_policy.py`
  - `READ_TOOLS` extended to agy's real read step types; new `NEUTRAL_TOOLS` for
    non-authoring steps; everything else still denied. Deny reason now names the
    tool and the allowed write roots. Fixes F5.
- Tests: +5 regressions (`tests/test_active_model_guard.py`,
  `tests/test_active_model_policy.py`) — invocation arming, no false arming on a
  mid-sentence mention, one-shot rules injection, neutral vs unknown tool,
  space-in-path helper, mirrored-install byte identity. 87 passed.

## Live verification after the fix

Direct `agy -p "/visual-prompt:visual-prompt '<file>' --no-video --no-music"`:

- `.visual-prompt-primary.json` created in the conversation's artifact dir at
  step 1 — armed before the model's first action.
- `VISUAL-PROMPT GUARDED …` injected as `EPHEMERAL_MESSAGE` at step 1.
- A composed shell command was denied (`runtime generator shell composition is
  forbidden`); the model self-corrected and continued.
- A second run (`--images 4`) completed the **whole pipeline** under the armed
  guard and produced `thu-nghiem_image_prompts.txt`. Three denials occurred, each
  self-corrected by the model within one turn (composed shell, wrong helper path,
  duplicate `--input`).
- Provenance chain proven live: `scene-plan.md` + `scene-001..004.md` each have a
  matching SHA-256 record from the primary conversation (5 records, no duplicates
  despite the double hook firing).
  `check_run_legit --require-authorship` → `OK: legit run`, exit 0.
- Negative test: appending one line to `scene-002.md` outside the guard →
  `FAIL (bypass/shallow): scene-002.md thiếu provenance khớp SHA-256`.
- Scenes are genuinely distinct (`scene-002` vs `scene-003` similarity 0.446), so
  the guard forces per-scene authorship without pushing the model into templates.
- Agy hit a context CHECKPOINT mid-run; arming survived it (head scan + state
  file), which the old tail-only marker scan would not have.

## Round 2 — the five residual items, closed

| # | Item | Resolution |
|---|------|------------|
| F6 | Workspace `.agents/hooks.json` | **Disproven and documented.** A probe hook placed there never fired, print or interactive. Two paths *do* load — the global config and the imported plugin's own `hooks.json` — which is the real reason every hook event fires twice. Plan phase-01, `SKILL.md` and `README.md` corrected. |
| F7 | Stale plugin copy | `setup.sh` now repoints `commands/`, `prompts/`, `references/`, `agents/`, `SKILL.md`, `gemini-extension.json`, `plugin.json`, `hooks.json` inside `~/.gemini/config/plugins/visual-prompt/` at the repo (originals moved aside, never deleted). Applied; the contract the model reads is now in sync. **First attempt put the backup inside `plugins/`, where Agy scanned it as another plugin, registered its `hooks.json`, failed to resolve the relative command, and degraded into permission prompts that hung two batch runs.** Backups now live in `~/.gemini/config/vp-plugin-backups/`. |
| F9 | Batch never run under the guard | **The batch driver was broken.** Commit `9de1c08` replaced `--dangerously-skip-permissions` with `--sandbox`; `--mode accept-edits` auto-approves file edits only, so the first `run_command` surfaced `Surfacing tool confirmation: "Bash"` and waited for a human that an unattended batch never provides — every batch run would have hung until its 4h deadline. Restored `--dangerously-skip-permissions` **alongside** `--sandbox` (the combination already used elsewhere on this machine): permission prompts were never the safety layer here, the PreToolUse guard is, and it keeps denying with prompts off. Added as a backstop: bounded idle nudges (2 silent 90s rounds → nudge, max 4, then fail fast into the existing retry path) so a genuinely stalled session costs ~12 min instead of 4h. |
| Gate skipping | Run could end with gates unrun | New **`Stop` hook**: a guarded run that authored scenes cannot end while `check_run_legit --require-authorship` **or** `check_prompt_similarity` fails. Bounded to `MAX_STOP_HOLDS = 2` counted per `executionNum` (the duplicate hook registration must not burn the budget), skipped for `--plan-only`/worker sessions via `VP_GUARD_STOP_GATE=0`, and never fired on errors, cancellations or step-limit stops — so it cannot loop. |
| Scene budget | 120 images for a 297-word file | `calc_scene_count` now caps the 120..150 band at one scene per 50 words (`grounding_capped` flag in the JSON). Sources ≥6000 words — every normal batch file — are unchanged; only short sources stop being asked to fabricate. |

Round-2 tests: 94 passed (Stop hold/release/bounded-per-execution, template-stamped
output held, error and plan-only stops never held, scene-plan alone does not arm
the gate, scene-budget curve).

Two further defects surfaced only by running the batch to completion:

- **Marker hang.** When every expected output exists but the model never emits
  `BATCH_RUN_COMPLETE`, the harness asked once and then waited out its 4h deadline
  (the idle path is skipped while `ready` is true). It now re-asks up to 3 times
  and then accepts the artifacts, letting the driver's gate battery decide.
- **Hand-written helper scratch.** The model wrote `.work/chapters_qa.json` itself
  instead of running `assemble_qa.py` — which is also what emits `<stem>_qa.txt`,
  so the run looked done to the model, failed the driver's output check, and cost
  a full `--force-redo` retry. `chapters.json` and `chapters_qa.json` are now
  guard-denied for the write tool while the helpers' own output still passes.
  Confirmed live: retry 2 produced `chapters.json` via `load_input.py`, which
  run 1 never did.

Round-2 live checks:

- `~/.gemini/config/plugins/visual-prompt/commands/visual-prompt.toml` now diffs
  clean against the repo; `agy` starts with zero hook errors.
- `agy agent` still lists `visual-prompt-writer`, so the batch preflight passes.
- The idle nudge fires exactly as designed (`agy: idle — nudging (1/3)`) after
  three silent rounds; threshold since tightened to two rounds because Agy models
  routinely yield their turn after a denied tool call.
- The `Stop` gate is registered in all three hook configs and passes its unit
  suite, but has not yet held a real Agy session — no live run has ended with a
  failing gate since it was added.
- Full batch run under the guard: idle nudge woke a yielded session, the model
  emitted the completion marker, the driver caught the missing `_qa.txt` and
  retried, and retry 2 produced complete artifacts. Gates on those artifacts:
  `check_run_legit --require-authorship` → OK, similarity → 0 violations over
  5 scenes, provenance → 17 records covering every scene file, none missing.
  The run was stopped by hand at the marker-hang point described above, which is
  the defect the same round fixed; the fix itself is therefore untested live.

## Residual risk / not fixed

- F8 (leftover smoke dir inside the old plugin copy) is now in the moved-aside
  backup under `~/.gemini/config/plugins/.visual-prompt-replaced-*`; delete that
  backup once the new symlink layout is confirmed good.
- Direct-run write scoping still depends on the launch directory: if agy is
  launched somewhere other than the input file's folder and the folder is not in
  `workspacePaths`, `.work` writes are denied. The denial now names the roots.
- Agy itself intermittently emits a malformed `run_command` payload
  (`WaitMsBeforeAsync` sent as a string) which costs the model a turn. Not ours to
  fix; the idle nudge keeps it from turning into a dead run.
- The scene-budget cap changes output for sources under ~6000 words only. Longer
  files keep the previous 120..150 band exactly.
- Cosmetic, unfixed: the model fills the scene frontmatter's `cache_key: <sha1>`
  field with `fakehash1..5`. Nothing reads that field for image scenes, so outputs
  are unaffected — but the contract asks for a hash and gets a placeholder, which
  is the kind of tell worth watching.
