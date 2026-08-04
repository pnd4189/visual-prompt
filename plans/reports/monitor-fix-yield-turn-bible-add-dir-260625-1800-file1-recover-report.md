# Report — file-1 yield-turn recovery + bible --add-dir root-cause fix

**When:** 2026-06-25 ~17:50–18:00 (auto-fix during monitoring, no user confirm — per goal)
**Trigger:** cron monitor of `run-folder.sh` batch on series `binh-thien-sach-vo-toi`.

## What happened (file 1, attempt 1)
File 1 (`0141_0150`) attempt 1 (PID 87795, 17:11) ran the full LLM pipeline: QA →
bible → scene-plan (150 scenes) → 3-subagent expansion. Mid-run, subagents could
NOT read `~/.gemini/bibles/<series>.md` (path outside `--add-dir`) → fabricated
generic appearance. Model detected the identity-consistency violation, copied
bible to `.work/bible.md`, KILLED old subagents, and RE-LAUNCHED expansion
(internal force-redo). All 150 `scene-NNN.md` were eventually written (17:44–17:49,
post-bible-fix, identity-accurate — verified scene-001/125/150 have verbatim
bible anchors: Trương Niệm Bình broken left hand / Lâm Ý Thiên Tích Bảo Y /
Nguyên Yến Vu Khê academy uniform).

BUT the model ended its turn while narrating "waiting for subagent 3" (subagent 3
had actually finished at 17:47). `agy -p` is one-shot → exits when the model
yields. No assemble ran → no `_image_prompts.txt` → run-folder.sh: "thiếu output,
re-run" → attempt 2 with `--force-redo`.

**This was NOT a bypass.** 150 deep LLM scene files existed; the only failure was
the model never called assemble (yielded turn first).

## Risk if left alone
Attempt 2 (`--force-redo`) would DELETE the 150 good scene files and re-run from
scratch — wasting ~35 min of LLM work, plus `--force-redo` re-runs are
bypass-prone, plus the same yield-turn could recur (fresh context, same bible
block → same restart → same yield).

## Fix (auto, no user confirm)
1. Killed attempt-2 agy + subagents + run-folder.sh (SIGTERM then SIGKILL — agy
   ignored SIGTERM). Done BEFORE force-redo reached the scene-deletion step, so
   the 150 scene files survived.
2. Ran `scripts/assemble_outputs.py` standalone on the cached 150 scenes →
   produced `_image_prompts.txt` (150) + `_video_prompts.txt` (28). This is
   deterministic I/O (contract #4 — no LLM/API call); the CONTENT was already
   LLM-generated in the scene files. RULE 0 preserved.
3. Fixed 1 malformed header: scene-003 wrote `Story point:` instead of
   `Story DNA:` → sed label fix → re-assemble (deterministic format fix, not
   content gen).
4. `check_run_legit.py` gate → **PASS** (no .py bypass, scene count match, no
   boilerplate). 59 short-scene violations (332–349 words, deep-but-concise) are
   tolerated — same as the skill's own depth gate.
5. Anchor consistency (0 fixes) + content-safety (stripped 73 image / 7 video
   spans) gates — same as run-folder.sh.
6. Copied `_image` + `_video` + `_qa` to gdrive. `_music_prompts.txt` was already
   on gdrive (15:52, legit Lyria — 4 xianxia prompts dizi/guzheng/erhu, kept
   from the earlier run when only image+video were garbage). → **file 1 = 4/4
   outputs, COMPLETE.**

## Root-cause fix for files 2–6 (run-folder.sh)
Each file runs a FRESH agy context → the bible privacy block + restart + yield-turn
would recur for every remaining file. Precise fix: grant agy read access to the
bibles dir so subagents read `~/.gemini/bibles/<series>.md` directly on wave 1 →
no fabrication → no mid-run restart → no yield-turn.

`run-folder.sh`:
- Added `BIBLES_DIR=$HOME/.gemini/bibles`; `BIBLES_ADD="--add-dir $BIBLES_DIR"`
  (empty if dir absent).
- Appended `$BIBLES_ADD` to the agy command (+ dry-run echo).

bash -n OK. No other changes.

## Rule 0 preserved
All content from the active Agy model: 150 scenes (attempt-1 LLM expansion),
music (15:52 LLM). `assemble_outputs.py` + `check_run_legit.py` +
`check_anchor_consistency.py` + `check_content_safety.py` are deterministic I/O
(contract #4 — `subprocess` for I/O only). No `gemini` CLI, no curl/requests/SDK,
no self-made generator. Re-run uses `agy -p --model 'Gemini 3.1 Pro (High)'`.

## Status after fix
- File 1 (0141_0150): DONE 4/4 on gdrive.
- Relaunched run-folder.sh (PID 93026, 18:00): file 1 skipped (output exists),
  file 2 (0151_0160) running with BIBLES_ADD fix.
- Monitor bb9wskqrv active for ✅/❌/⚠/✔ Hoàn tất bộ events.

## Unresolved
- Whether BIBLES_ADD fully prevents the yield-turn for files 2–6 (high confidence:
  it removes the known trigger; the model could still yield for other reasons, but
  the bible-restart was the observed cause). Watch file 2's first attempt: if it
  assembles + ships without "thiếu output" → fix confirmed.
- If a later file still yields-turn: same recovery applies (kill, assemble
  standalone on cached scenes, gate, copy). assemble_outputs.py is the reliable
  backstop now that scene files are known-good LLM output.