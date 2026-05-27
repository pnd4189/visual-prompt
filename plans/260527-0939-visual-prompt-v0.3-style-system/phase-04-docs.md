---
phase: 4
title: "Docs"
status: done
priority: P2
effort: "0.5d"
dependencies: [3]
---

# Phase 4: Docs

## Overview

Cập nhật SKILL.md + HUONG-DAN-SU-DUNG.md để tài liệu hoá hệ thống style: flag
`--style`, bước recommend tương tác, catalog, và lưu ý style accent phá nhất quán.

## Requirements
- Functional: user đọc docs hiểu cách chọn style (tương tác + flag), 18 style là
  gì, style nào hợp genre nào, cảnh báo accent/video.
- Non-functional: docs tiếng Việt, khớp hành vi thực tế sau Phase 1-3.

## Architecture
Workflow tăng từ 8 → có thêm STEP 3.5; cập nhật mọi chỗ liệt kê bước/flag.

## Related Code Files
- Modify: `SKILL.md`, `HUONG-DAN-SU-DUNG.md`

## Implementation Steps
1. `SKILL.md`:
   - version 0.2.0 → 0.3.0; description nhắc multi-style.
   - Workflow section: chèn bước "Style recommend + select" sau Genre detect.
   - Usage: thêm `[--style <id>]` vào dòng lệnh + giải thích.
   - File Layout: thêm `references/style-catalog.md`,
     `references/genre-style-recommendation.md`, `prompts/style-recommender.md`.
   - Limitations: thêm "style accent/video giữ nhất quán nhân vật kém — nên dùng
     title card/montage"; "headless run: không trả lời → fallback recommend #1, hoặc
     dùng --style"; "music score nền giờ theo music/score anchor của style".
2. `HUONG-DAN-SU-DUNG.md`:
   - Mục mới "Chọn style": cách tương tác + flag, bảng 18 style + category, bảng
     genre→recommend, lưu ý accent/video.
   - Cập nhật ví dụ lệnh + mô tả bước chạy.

## Success Criteria
- [ ] SKILL.md version 0.3.0, có bước style trong workflow + `--style` trong usage.
- [ ] File Layout liệt kê 3 file mới.
- [ ] HUONG-DAN-SU-DUNG.md có mục "Chọn style" + bảng 18 style + cảnh báo.
- [ ] Không còn mô tả "chỉ cinematic 4K" như style cố định duy nhất.

## Risk Assessment
- Docs lệch code nếu Phase 2/3 đổi tên flag/id → viết docs SAU khi Phase 3 xong,
  đối chiếu id thực trong style-catalog.
