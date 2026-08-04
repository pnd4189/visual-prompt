# Report — file-3 full bypass (lorem ipsum + video boilerplate) + video gate fix

**When:** 2026-06-26 ~09:04 (detected) → ~09:12 (fix + relaunch)
**Trigger:** user asked completion status → checked file 3 (running since 08:39 post-reboot relaunch).

## Context — reboot
Machine rebooted overnight (~07:10, uptime 1:29 at 09:04). The nohup batch was
killed, /tmp workdir cleared, session-only cron died. Files 1+2 safe on gdrive.
Relaunched 08:39 with the 3 prior fixes (BIBLES_ADD, no-tee, continuity
fast-path+timeout) all intact on disk. File 3 (0161_0170) started clean.

## File 3 — full bypass (NOT a hang-only issue)
agy (7564) wrote 144 scene files + 4 outputs at 08:48, then went IDLE (S state,
0.7% CPU, ep_poll, 4 children on ep_poll/futex) for 16+ min — no log since 08:39,
no exit (would have timed out at the 3h --print-timeout). On inspection the
outputs were GARBAGE, not just a hang:

- **Image (`_image_prompts.txt`, 509 KB):** every scene block is a generic
  template padded with **`lorem ipsum dolor sit amet consectetur adipiscing elit
  sed do eiusmod tempor incididunt ut labore et dolore magna aliqua`** repeated
  ~2× per section (Setting, Composition, Subject, Action, Style, Lighting,
  Atmosphere). `Subject:` holds the style description, not a character. Bold
  markdown headers (`**Camera:**`) — the proper expander uses plain `Camera:`.
  The image expander prompt (`@prompts/prompt-expander-image.md`) was NOT used.
- **Video (`_video_prompts.txt`):** all 24 video-tagged scenes have the IDENTICAL
  block — `**Subject:** Cultivators flying on glowing swords, flowing cloth
  physics` / `secret realm entrance` — a single template duplicated, not matching
  any scene's content (scene 001 is a miasma-forest battle). Video expander bypass.
- qa + music written (108 KB / 12 KB) — music looks structured (not checked deep).

This is WORSE than the file-1 bypass (which had boilerplate but no lorem ipsum).
The image-expansion subagent produced filler, the video-expansion subagent
produced one duplicated template.

## Root cause
Model/subagent behavior — the expander prompts were ignored (lorem ipsum filler +
identical video template). The 3 prior fixes (BIBLES_ADD, no-tee, continuity)
don't address content bypass. Why file 3 flaked when file 2 was deep (54 KB video,
28 distinct scenes) is unknown — model flakiness, not a config regression
(BIBLES_ADD was active on file 3 too; file 2 used it and was deep). The agy hang
after writing the garbage (idle on ep_poll) is likely the model's next API call
stuck — separate from the bypass, but both point at a flaky run.

## Fix — video boilerplate gate (check_run_legit.py)
The gate only checked IMAGE boilerplate (8-word ngram repeat). File 3's image was
ALREADY caught by it (144/144 blocks: the lorem-ipsum 8-word run repeats >5×
within each block). But video had NO check. Added:

- `--video <vid.txt>` arg (optional).
- Parse `--- SCENE N ---` blocks; normalize whitespace; if ≥4 video scenes and
  the most-common body is >50% of total → FAIL ("N/M video scene blocks identical
  (boilerplate template, video expander bypass)").
- `run-folder.sh` now passes `--video "${local_stem}_video_prompts.txt"` to the gate.

Validated on file-3's re-assembled output (24 identical video blocks):
`FAIL: 144/144 image boilerplate + 24/24 video identical` (exit 2). Catches the
bypass. bash -n / ast.parse OK.

## Recovery + relaunch
Killed hung agy 7564 + run-folder 7433 (SIGKILL; children cleaned). Relaunched
run-folder.sh (PID 13549, 09:12) — file 3's local_dir is rm -rf'd by run-folder's
fresh-dir step, so it re-expands from scratch under the gate. The 3-attempt retry
loop (attempt 1 plain, 2-3 `--force-redo`) handles a bypass: gate FAIL → re-run;
3× FAIL → die → escalate to user (model persistently defeats the contract).

## Rule 0 preserved
Gate + scripts are deterministic I/O (contract #4). Re-run uses `agy -p --model
'Gemini 3.1 Pro (High)'`. No `gemini` CLI / API / SDK. The gate edit adds a check,
not content generation.

## Status
- Files 1, 2: DONE 4/4 on gdrive.
- File 3: re-running fresh (PID 13549) under the video gate. Monitor bud40qtv6 +
  cron e7f50536 active.
- Files 4-6: pending. If file 3 ships deep, continue; if it bypasses 3× → die.

## Unresolved
- Whether file 3's bypass recurs on re-run (model flakiness vs systematic). If
  the lorem-ipsum + identical-video pattern repeats across attempts, the model is
  persistently bypassing the expander → auto-fix can't force deep output → report
  to user. Watch file 3 attempt-1 output depth.
- The agy hang (idle on ep_poll after writing outputs) — if it recurs, --print-
  -timeout 3h is a 3h wait; monitor + cron should catch it within 30 min for a
  manual kill (the gate then runs on whatever outputs exist).