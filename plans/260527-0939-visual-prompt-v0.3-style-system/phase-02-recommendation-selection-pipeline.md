---
phase: 2
title: "Recommendation + Selection + Pipeline"
status: done
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: Recommendation + Selection + Pipeline

## Overview

Thêm bảng gợi ý genre→style, prompt recommender, flag `--style`, bước tương tác
STEP 3.5, materialize `.work/active-style.md`, và đưa `style_hash` vào scene cache
key. Sau phase này pipeline đã CHỌN và GHI style; Phase 3 mới tiêu thụ.

## Requirements
- Functional:
  - no-flag → sau genre detect in recommend #1 + 2-3 alt + cảnh báo anchor → hỏi
    user (Enter = #1, hoặc gõ id khác).
  - `--style <id>` → validate id ∈ catalog → skip hỏi. Sai → lỗi VN liệt kê id.
  - Style đã chọn materialize ra `.work/active-style.md`; đổi style re-run →
    scene regenerate (cache bust qua `style_hash`).
- Non-functional: giữ LLM-loop, Python chỉ I/O; string user = VN.

## Architecture

### File mới
- `references/genre-style-recommendation.md` — bảng mềm 5 genre → #1 + alternatives
  + lý do (tách rời: chỉ gợi ý, mọi style vẫn hợp lệ). Nội dung từ brainstorm report.
- `prompts/style-recommender.md` — LLM prompt: input `genre` (+ optional sample) →
  output recommend #1 + 2-3 alt (đọc `references/genre-style-recommendation.md` +
  `references/style-catalog.md`) + cảnh báo nếu style là accent/video
  ("giữ nhất quán nhân vật kém — nên dùng title card/montage").

### Sửa `commands/visual-prompt.toml`
- STEP 0 flag parse: thêm `--style ([a-z0-9-]+)` → `style_override`. Update echo
  block + danh sách flag trong error "flag không hỗ trợ".
- STEP 3.5 (mới, sau STEP 3 genre detect, trước STEP 4):
  ```
  Nếu style_override set:
    - Validate id ∈ style-catalog (đọc bảng tra nhanh). Sai → HALT lỗi VN:
      "Lỗi: --style '<id>' không hợp lệ. Id hợp lệ: <list>"
    - chosen_style = style_override (không hỏi).
  Else:
    - Load @prompts/style-recommender.md với genre đã detect → in recommend.
    - HỎI user chọn (Enter = #1, hoặc nhập id). Validate. chosen_style = kết quả.
    - FALLBACK (headless / không có câu trả lời tương tác): chosen_style = recommend
      #1; in "Style mặc định: <id> (recommend cho <genre>). Override: --style <id>."
  Materialize: copy entry chosen_style từ style-catalog → .work/active-style.md
  (chỉ 1 entry, nguyên văn). style_hash = sha1(file_bytes(.work/active-style.md))[:12]
  → ghi .work/style.hash. Print: "Style: <id> (<category>)".
  ```
- STEP 5 cache (scene-plan): KHÔNG đổi (plan độc lập style).
- STEP 6 cache key scene đổi:
  `sha1(qa_hash + bible_hash + plan_hash + style_hash + serialize(scene_row))[:16]`.
  Cập nhật cả mô tả mismatch warning để nhắc "style changed".

### Vì sao materialize (không lazy-load)
Khớp pattern hash sẵn có (qa/bible/plan). `style_hash` cho cache invalidation
"free"; expander đọc 1 file cố định thay vì tra catalog mỗi scene.

## Related Code Files
- Create: `references/genre-style-recommendation.md`, `prompts/style-recommender.md`
- Modify: `commands/visual-prompt.toml`

## Implementation Steps
1. Viết `genre-style-recommendation.md` (bảng từ brainstorm report §Genre→style).
2. Viết `prompts/style-recommender.md` (role, input genre, output format recommend
   + alt + cảnh báo accent/video, đọc 2 reference).
3. `visual-prompt.toml` STEP 0: thêm regex `--style`, update echo + error list.
4. `visual-prompt.toml`: chèn STEP 3.5 (logic trên) giữa STEP 3 và STEP 4.
5. `visual-prompt.toml` STEP 6: thêm `style_hash` vào công thức cache_key + sửa
   text warning mismatch.
6. Cập nhật POST-RUN SUMMARY: thêm dòng `Style: <id> (<category>)`.

<!-- Updated: Validation Session 1 - default=recommend #1, headless fallback #1 (Q1,Q2) -->

## Success Criteria
- [ ] `--style donghua-xianxia` → skip hỏi, materialize đúng entry.
- [ ] `--style sai-id` → HALT, in lỗi VN + liệt kê id hợp lệ.
- [ ] no-flag → in recommend #1 + alt + cảnh báo (nếu accent/video) → hỏi → chọn.
- [ ] no-flag headless / không trả lời → fallback recommend #1 + in cách override.
- [ ] recommend #1 đúng bảng genre-style-recommendation (vd tiên hiệp → donghua-xianxia).
- [ ] `.work/active-style.md` chứa đúng 1 entry; `.work/style.hash` tồn tại.
- [ ] Scene cache_key chứa `style_hash`; đổi `--style` re-run → scene regenerate.

## Risk Assessment
- Bước hỏi giả định CLI foreground (đúng với cách skill chạy). Nếu chạy headless,
  user phải dùng `--style`; tài liệu hoá ở Phase 4.
- Cache key đổi → run cũ (không có style_hash) sẽ mismatch → regenerate 1 lần. OK,
  ghi chú trong warning.
