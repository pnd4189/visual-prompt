---
phase: 5
title: "TOML Wiring Music Plan Persistence"
status: completed
effort: "L"
---

# Phase 5: TOML Wiring Music Plan Persistence

## Overview
Wire gates into `commands/visual-prompt.toml` pipeline + persist music
segmentation. Discipline: TOML additions are POINTERS to deterministic gates,
kept tight (contract already 34KB — no bloat).

## Related Code Files
- Modify: `commands/visual-prompt.toml`
- Modify: `scripts/validate_artifacts.py` (music-plan aware `--check music`)

## Implementation Steps
1. Header: `v0.9.2` → `v0.10.0`.
2. STEP 5.5: add `duplicate_synopsis` to the row-targeted revise branch
   (violations with scene_ids → rewrite those rows with different beats).
3. STEP 6.5 — music-plan persistence (closes SKILL.md limitation):
   - LLM segments ONCE → write `.work/music-plan.md`, frontmatter
     `cache_key = sha1(qa_hash + genre + plan_hash + music_n)[:16]`, body =
     region table `{loop_index, chapter_start, chapter_end, mood}`.
   - On rerun: cache match → reuse segmentation verbatim, only regenerate
     missing/stale `music-NNN.md`. `--force-redo` deletes music-plan.md too.
   - Per-loop cache_key now uses region_spec FROM music-plan (deterministic).
4. `validate_artifacts.py`: `--check music` reads expected regions from
   `.work/music-plan.md` when present (fallback: `--expected-music N` as today).
5. NEW STEP 7.3 — SIMILARITY GATE (after depth gate, BEFORE content-safety
   `--fix`, so safety edits are never overwritten by re-assemble):
   ```
   python3 scripts/check_prompt_similarity.py --image "<stem>_image_prompts.txt" \
     [--video "<stem>_video_prompts.txt"]   # skip khi no_video
   python3 scripts/check_prompt_similarity.py --music "<stem>_music_prompts.txt"
   ```
   Bounded loop ≤2: violations → rm các `.work/scene-NNN.md` trong
   `rewrite_scene_ids` (giữ scene id nhỏ nhất mỗi cụm) → re-expand từng scene
   qua LLM expander, BẮT BUỘC đính kèm `banned_phrases` vào context ("các cụm
   sau đã dùng ở scene khác, TUYỆT ĐỐI không dùng lại") → re-assemble →
   re-check. Music violations tương tự với music-NNN.md. Sau 2 lượt → HALT,
   không ship output còn violation. KHÔNG tự tay sửa .txt.
6. NEW STEP 7.8 — VISUAL-HISTORY UPDATE (chỉ khi --series; sau content-safety):
   ```
   python3 scripts/check_prompt_similarity.py --extract-history \
     --image "<stem>_image_prompts.txt" --music "<stem>_music_prompts.txt" \
     --history ~/.gemini/bibles/<series>-visual-history.md
   ```
   Pure I/O — hợp lệ RULE 0. STEP 5 planner + STEP 6.5 music builder context:
   đọc file này nếu tồn tại (truyền như bible).
7. STEP 8 self-audit: thêm lệnh similarity check + confirmation item #6:
   "similarity gate exit 0; KHÔNG sửa gate/threshold để né; chưa đạt → KHÔNG
   báo hoàn tất."

## Success Criteria
- [x] `tomllib` parse OK; net TOML growth ≤3KB
- [x] Gate order: depth → similarity(rewrite→re-assemble) → safety --fix → history → audit
- [x] music-plan.md cache semantics specified (create/reuse/force-redo)
- [x] validate_artifacts music-plan aware, py_compile clean

## Risk Assessment
Rewrite loop non-convergence when plan rows identical → Phase 3 gate blocks at
Pass 1 + banned_phrases forces divergence; residual is rejected after bounded retries.
More end-of-run LLM work → slight yield-turn risk; driver (Phase 6) re-runs
resume-safe.
