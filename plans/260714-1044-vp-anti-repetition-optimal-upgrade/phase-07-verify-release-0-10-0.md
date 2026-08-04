---
phase: 7
title: "Verify Release 0-10-0"
status: in-progress
effort: "M"
---

# Phase 7: Verify Release 0-10-0

## Overview
End-to-end verification against real chap16 data + fixtures, docs/version sync,
final commit. Symlink install = live on commit (no redeploy).

## Implementation Steps
1. Verification matrix:
   - chap16 fixture (path from Phase 1) → `--image` exit 2; Camera exact ≈38,
     Setting/Atmosphere exact ≈106 (khớp full_report.md); rewrite_scene_ids +
     banned_phrases non-empty.
   - Clean fixture → exit 0.
   - Stride-11 plan fixture → duplicate_synopsis.
   - `--extract-history` ×2 → idempotent, cap 150/section.
   - `py_compile` mọi script sửa/mới; `tomllib` parse TOML; `bash -n` run-folder.sh.
   - `check_run_legit.py --purge-skill-dir .` → 0 rogue (script mới trong allowlist).
2. SKILL.md: version 0.10.0; workflow bullets cho STEP 7.3/7.8 + music-plan;
   XÓA limitation "Music resume is best-effort"; File Layout: 15 helpers + 2 drivers;
   Philosophy: 1 bullet "similarity outcome-gate + visual-history (v0.10.0)".
3. `gemini-extension.json`: 0.10.0 (nhớ: version bump 2 chỗ — memory rule).
4. HUONG-DAN-SU-DUNG.md: 1 đoạn ngắn về visual-history file + gate mới (nếu §
   tồn tại sẵn cấu trúc phù hợp; không viết dài).
5. Commit 2: `feat: outcome-based anti-repetition gates, per-series visual
   history, music-plan persistence` (body liệt kê gate + policy).
6. Update memory: check-run-legit gate memory (+similarity gate), new memory
   cho visual-history mechanism + thresholds cần tune.
7. Báo user: danh sách quarantine cần duyệt + 3 unresolved (tune 0.95 sau
   2-3 run; có siết band 0.6-0.95 không; Windows setup.bat).

## Success Criteria
- [ ] Toàn bộ verification matrix pass, số liệu chap16 khớp full_report.md
- [x] Version 0.10.0 đồng bộ 3 file; limitation music-resume đã xóa
- [ ] Commit 2 landed; memory updated
- [ ] Không còn uncommitted diff nào ngoài quarantine dirs

## Risk Assessment
Ngưỡng 0.95/counts chưa tune bằng run thật — có flags override, theo dõi 2-3
run đầu (ghi trong unresolved). Windows copy-install cần re-run setup.bat.
