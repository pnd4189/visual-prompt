---
title: "Agy Guard Arming Fix"
date: "2026-08-09 17:58"
severity: "High"
component: "Agy active-model runtime guard"
status: "Resolved"
---

# Agy Guard Arming Fix

## Context

Audit of `9c37715..e81daa8` against plan `260808-visual-prompt-active-model-runtime-guard`.
The guard's contract turned out to be right — flat camelCase payloads, real tool
names, provenance logging, write scoping all match Agy 1.1.11, confirmed by
capturing live hook payloads. What was wrong was when it switched on.

## What Happened

The guard armed on `VP_GUARD_ACTIVE=1` (batch only) or on the marker string from
`commands/visual-prompt.toml` appearing in the transcript. But Agy writes only the
raw `/visual-prompt:visual-prompt …` user turn into `transcript_full.jsonl`; the
expanded command prompt never lands there. The marker reached the transcript only
when the model chose to read the TOML itself — so the guard was armed by the same
diligence it exists to enforce, and a model that skipped the contract ran
unguarded. Direct invocations therefore had no enforcement at all.

Arming now keys off the user's invocation line, which is present at step 0
regardless of what the model does. Three further blockers surfaced once the guard
actually ran: an unquoted absolute helper path split on the space in the skill
root, mirrored installs (Windows copy, Agy plugin copy) failed the identity check
on every canonical helper, and Agy's real read/neutral step types were outside the
allowlist. The rules message was also unreachable, since it only fired at
invocation 0 while arming happened later.

## Reflection

Every layer was built correctly and none of it was connected to the trigger. The
lesson is the same one as last time, one level down: a fail-closed gate that
depends on cooperative behavior to switch on is not fail-closed. Verifying the
trigger deserved as much attention as verifying the rules.

## Decisions

- Arm on the raw invocation turn; keep the marker as a secondary signal.
- Announce the rules once, on the first armed turn, via the exclusive state claim.
- Identify canonical helpers by name plus byte identity, not by install prefix.
- Keep deny-by-default over the tool namespace, with an explicit neutral list.

## Round 2 — closing the residual items

Five leftovers were closed in the same session.

`.agents/hooks.json` turned out to be dead weight — a probe placed there never
fired in either mode. Two paths do load, the global config and the imported
plugin's own `hooks.json`, and that is the real reason every hook event arrives
twice. Docs now say that instead of claiming three interchangeable paths.

`setup.sh` repoints the imported plugin copy's `commands/`, `prompts/`,
`references/` and `agents/` at the repo, so the contract the model reads can no
longer drift behind the source. The first version of that change moved the
originals to a backup **inside** `plugins/`, which Agy promptly scanned as another
plugin; its `hooks.json` registered, its relative command did not resolve, the
PreToolUse hook failed, and Agy fell back to interactive permission prompts that
hung two unattended batch runs. The symptom looked exactly like the stall being
investigated, which is the uncomfortable part: a self-inflicted fault that
imitates the fault under study is very easy to file as evidence. Backups now live
outside `plugins/`.

The batch driver ran for the first time under the guard and turned out to be
broken outright. The previous session had swapped `--dangerously-skip-permissions`
for `--sandbox`, but `--mode accept-edits` auto-approves file edits only: the
first `run_command` raised `Surfacing tool confirmation: "Bash"` and waited for a
human who, in an unattended batch, never arrives. Every batch run would have hung
until its four-hour deadline. Permission prompts were never the safety layer here
— the PreToolUse guard is, and it keeps denying with prompts disabled — so both
flags now ride together, the way the pdf-convert runner on this machine already
does it.

Chasing that took two wrong turns worth recording. The first idle detector keyed
on "no bytes received from the terminal", which never happens because an idle Agy
TUI keeps redrawing; liveness now comes from artifact mtimes. And the nudge itself
cannot rescue a confirmation dialog — typing a sentence into a y/n prompt does
nothing — so its real value is the bound it puts on a stall: four nudges, then
fail into the normal retry path in about twelve minutes instead of four hours.

Two quality gaps closed with it. A `Stop` hook refuses to end a guarded run while
`check_run_legit --require-authorship` or `check_prompt_similarity` still fails —
bounded to two holds, and never triggered by errors, cancellations or step limits,
so it cannot become a loop. And `calc_scene_count` no longer demands 120 images
from a 297-word source: the band is capped at one scene per 50 words, which leaves
every normal batch file untouched and stops short sources from forcing the model
to choose between fabricating and halting on turn one.

Running the batch all the way through turned up two more. When every output
exists but the model never prints the completion marker, the harness asked once
and then waited out its deadline — it now re-asks three times and accepts the
artifacts, since the driver's own gates are the real acceptance test. And the
model had hand-written `.work/chapters_qa.json` instead of running
`assemble_qa.py`, which is also what emits `<stem>_qa.txt`; the run looked
finished to the model, failed the driver's output check, and cost a full retry.
Both files are now guard-denied for the write tool while the helpers' own output
passes, and the retry proved it: run 2 produced `chapters.json` through
`load_input.py`, which run 1 never did.

## Next

Watch the first production batch for nudge frequency — if `idle — nudging` shows
up on healthy runs, the three-round threshold is too tight. The moved-aside plugin
copies under `~/.gemini/config/plugins/.visual-prompt-replaced-*` can be deleted
once the symlink layout is confirmed good.
