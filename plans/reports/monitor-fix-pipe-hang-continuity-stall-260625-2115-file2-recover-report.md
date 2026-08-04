# Report — file-2 pipe-hang recover + no-tee fix + continuity gdrive-stall fix

**When:** 2026-06-25 ~21:00–21:15 (auto-fix during monitoring, no user confirm)
**Trigger:** cron monitor — file 2 (0151_0160) ran 3+ h vs ~40 min for file 1.

## File 2 — what happened
File 2's agy ran the full LLM pipeline (QA, bible, scene-plan, 3-subagent
expansion of 150 scenes). It hit `Error: timed out waiting for response` (agy's
internal model-response timeout) AFTER writing all 4 outputs to the local workdir
(18:48: image 512 KB, video 54 KB, music 3.2 KB, qa 108 KB) + 150 scene files.
agy then exited — but `run-folder.sh` was stuck and never reached the gate.

**Root cause (pipe hang):** the run line was `( cd … && agy -p … ) 2>&1 | tee "$log"`.
When agy exited, a lingering child that had inherited the pipe's write-end kept
tee's stdin open, so tee never read EOF, the pipeline never completed, and
run-folder.sh stalled at the `| tee` line (verified: tee 93136 in S state on
pipe read, agy dead, run-folder blocked). The `$log` temp file was pointless —
tee wrote it then `rm -f "$log"` deleted it unread; the real log is `~/vp-batch.log`
via the nohup redirect. So the pipe bought nothing and could hang the batch.

The model also narrated "viết mã khôi phục tự động" / "23 cảnh bị lỗi → nhánh
riêng" — but `.work` had **no .py** at end and the gate PASSED (150 deep scenes,
no bypass, no boilerplate; scene-001 is a legit "Subject: None." env shot, 10
sections, 297 w). So no bypass — just the pipe hang.

## Fix 1 — file-2 recover (manual, like file 1)
Killed stuck tee + run-folder. Ran gates manually: `check_run_legit.py` PASS;
`check_anchor_consistency --fix` normalized 55 (image) + 10 (video) off-bible
anchors; `check_content_safety --fix` stripped 2 (image) + 9 (video) spans.
Copied all 4 outputs to gdrive. File 2 = 4/4 DONE.

## Fix 2 — no-tee (run-folder.sh)
Removed `| tee "$log"` → direct `( agy ) 2>&1` redirect. No pipe ⇒ no lingering
child can hold a write-end ⇒ no hang. Removed the now-dead `log=$(mktemp)` +
`rm -f "$log"`. Verified: file-3 run-folder's only child is `agy` (no tee).

## Fix 3 — continuity gdrive-stall (check_previous_continuity.py + run-folder.sh)
After the no-tee relaunch, file 3 stalled at the continuity check:
`check_previous_continuity.py` (PID 112144) entered **D state (uninterruptible
disk sleep)**, wchan `request_wait_answer`, fd open on `BẢN DỊCH/Chap 1…`.
SIGKILL queued but can't act until FUSE returns (could be hours). Cause:
`_candidate_files` did `root.iterdir()` + `directory.glob('*.txt')` across every
sibling subdir under `BẢN DỊCH` on the gdrive FUSE mount — the known FUSE stall.
It eagerly collects up to 200 candidates BEFORE checking any, so even though the
previous chapter (ch.160) sat in the input folder, the scan hit a large sibling
folder and hung.

- `check_previous_continuity.py`: added a **fast path** — scan
  `input_path.parent.glob('*.txt')` first (only the current batch's files, a
  handful; for a sequential batch file N-1 is right here). Return if found.
  The broad sibling-dir scan is now a **fallback** only when the input folder
  had no match. Tested on file 3: found `0151_0160_qa.txt` (ch.160),
  inspected 2 candidates, 36 s, no stall.
- `run-folder.sh`: wrapped the call in `timeout 60` so the broad-scan fallback
  can't block the batch (on timeout, proceeds without a continuity excerpt; the
  skill's own STEP 1.25 still runs).

## Status after fixes
- File 1, 2: DONE 4/4 on gdrive.
- Relaunch (PID 113082, 21:15): skipped 1+2, continuity fast-path found
  `0151_0160_qa.txt`, file 3 (0161_0170) running with all 3 fixes active
  (BIBLES_ADD `--add-dir ~/.gemini/bibles`; no-tee; continuity fast-path+timeout).
- Files 4-6 pending. The D-state orphan python (112144) is harmless (run-folder
  is dead); will die when FUSE resolves. Not unmounting gdrive (would disrupt the
  user's separate interactive agy session 91604).

## Rule 0 preserved
All content from active Agy model (Gemini 3.1 Pro High): file-2 scenes + music
LLM-generated; recovery used only deterministic I/O scripts (assemble_outputs,
check_run_legit, check_anchor_consistency, check_content_safety — contract #4).
No `gemini` CLI / API / SDK. The 2 script edits are I/O-path fixes (no content
generation). `check_previous_continuity.py` only locates + reads files.

## Unresolved
- Whether the agy `timed out waiting for response` recurs for files 3-6 (it hit
  file 2 at the end of a long expansion). If it does, the no-tee fix means
  run-folder.sh now proceeds to the gate instead of hanging — and the same
  manual-recover (gate + copy) applies if outputs exist. Watch for ✅ 3/6.
- FUSE latency for the continuity fast-path was 36 s on file 3 (listing the input
  folder + reading 2 QA files). Within the 60 s timeout, but if FUSE slows
  further a later file could time out and lose the continuity excerpt (minor).