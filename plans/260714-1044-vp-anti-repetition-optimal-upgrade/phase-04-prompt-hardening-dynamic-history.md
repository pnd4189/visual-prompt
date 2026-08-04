---
phase: 4
title: "Prompt Hardening Dynamic History"
status: completed
effort: "M"
---

# Phase 4: Prompt Hardening Dynamic History

## Overview
Replace series-specific hardcoded avoid-lists (uncommitted +210 lines from
manual session) with dynamic visual-history references; add hard uniqueness
constraints to the image expander. Prompts are the SOFT layer — gates (Phases
2/3/5/6) enforce; prompts steer.

## Related Code Files
- Modify: `prompts/scene-planner.md` (uncommitted +158 lines to replace)
- Modify: `prompts/music-prompt-builder.md` (uncommitted +52 lines to trim)
- Modify: `prompts/prompt-expander-image.md`

## Implementation Steps
1. `scene-planner.md`: DELETE hardcoded §1-§3 lists (camera framings/settings/
   actions of Mã Lực Thuật series). KEEP generic §4 General Instruction. ADD:
   - "Nếu context có `visual-history` (per-series): tránh dùng lại NGUYÊN VĂN
     các mô tả camera/setting/action motif trong đó. Địa điểm tái xuất hợp lệ
     PHẢI được tả lại bằng góc máy + chi tiết MỚI (không cấm địa điểm —
     'unless the plot explicitly requires it' giữ nguyên tinh thần)."
   - Plan-side rule: không có 2 rows synopsis gần giống ở BẤT KỲ khoảng cách
     nào (gate `duplicate_synopsis` sẽ reject); xoay camera family giữa các
     row liền kề.
2. `music-prompt-builder.md`: KEEP added HARD DIVERSITY RULE + "template là
   sườn nội dung, không phải form cú pháp" note + generic §3. DELETE hardcoded
   mood/intro/tag lists. ADD: đọc `music intros used` + `music tags used`
   sections của visual-history (nếu được truyền) — không lặp intro nguyên văn,
   hạn chế tag đã dùng dày đặc.
3. `prompt-expander-image.md`: ADD hard constraints block + self-check #10:
   - Cấm reuse nguyên câu/cụm >8 từ từ bất kỳ scene khác trong run, mọi section
     TRỪ Subject anchor / Style block / Negative (verbatim by-design).
   - Camera: chọn theo beat của CẢNH NÀY; cấm xoay vòng một câu camera formula.
   - Story DNA / Atmosphere: nhịp động của khoảnh khắc, cấm summary tĩnh của
     cả chương dùng chung nhiều scene.
   - Self-check #10: so mọi section (trừ 3 verbatim) với các scene bạn đã viết
     trong batch — trùng nguyên câu → REWRITE trước khi ghi file.
   - Note: cross-batch dup do subagent không thấy nhau → STEP 7.3 gate bắt
     (không phải trách nhiệm subagent).

## Success Criteria
- [x] Không còn nội dung series-specific nào trong 3 prompt files
- [x] Generic rules từ manual session được GIỮ (không mất công sức trước đó)
- [x] Expander có đủ: >8-word ban, camera-per-beat, dynamic DNA, self-check #10

## Risk Assessment
Prompt-only layer — model có thể lờ; chấp nhận vì gates enforce. Đừng phình
file quá mức (mỗi file thêm ≤25 dòng net sau khi xóa hardcode).
