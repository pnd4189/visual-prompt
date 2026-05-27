---
phase: 3
title: "Decouple Expanders + References"
status: done
priority: P1
effort: "0.5d"
dependencies: [2]
---

# Phase 3: Decouple Expanders + References

## Overview

Gỡ hardcode "cinematic 4K + Crouching Tiger/Hero" khỏi expander + reference, cho
image/video prompt đọc style từ `.work/active-style.md`. Tái cấu trúc negative để
chèn style negatives (nới cap 20 → 24). Music score cũng decouple theo style.

## Requirements
- Functional: Style section của mọi prompt dùng `Style block` + `reference anchors`
  của style đã chọn; negative gồm style negatives từ catalog.
- Non-functional: `painterly-realism-cinematic` reproduce output v0.2 (regression).

## Architecture

### Gỡ hardcode (breaking)
- `prompts/prompt-expander-image.md`:
  - Step task: thêm "Load `.work/active-style.md`; dùng `Style block` cho Style
    section, `reference anchors` thay cinema reference."
  - Bỏ Step 7 cũ ("cite Crouching Tiger/Hero mandatory") → thay "cite reference
    anchor của style đang chọn".
  - Self-check #4: "Crouching Tiger/Hero appears" → "reference anchor của style
    xuất hiện trong Style".
- `prompts/prompt-expander-video.md`: tương tự self-check #7 + Style & Ambiance.
- `references/visual-prompt-template.md`: phần Style spec + rule "Cinema reference
  REQUIRED → Crouching Tiger/Hero" → "dùng Style block của style đang chọn; cite
  reference anchor của style". IMAGE/VIDEO EXAMPLE giữ làm ví dụ cho
  `painterly-realism-cinematic` (ghi chú rõ "ví dụ cho style painterly-realism").
- `references/genre-keywords.md`: mỗi genre dòng "Style anchor: <phim>" → "Default
  recommended style: <id> (xem style-catalog)". Bỏ ép phim.

### Negative restructure (nới cap → 24, Q3 validation)
`references/negative-lists.md`:
- Layer 1 universal anti-Western: giữ **10** (không rút — là mục đích gốc).
- Layer 2 genre: giữ **5**.
- Layer 3 AI-defense: giữ **5**.
- Layer 4 (mới) style negatives: **4** — lấy từ `style negatives` của
  `.work/active-style.md`.
- Tổng = 10+5+5+4 = **24**. Đổi "Max 20 items" → "Max 24 items"; cập nhật
  "Composed Example" + ghi chú expander đọc Layer 4 từ active-style.

### Music score decouple (Q4 validation)
`prompts/music-prompt-builder.md` + `references/music-mood-mapping.md` đang hardcode
"Crouching Tiger / Hero score" làm base style nhạc. Sửa:
- music-prompt-builder: load `.work/active-style.md`; nếu có `music/score anchor`
  thì override "Base style" register bằng anchor đó.
- music-mood-mapping: các dòng "Base style: *...Crouching Tiger score*" → đổi thành
  "Base style: *<default theo genre>; override bằng music/score anchor của style*".
- Music segmentation/mood/arc logic GIỮ NGUYÊN (chỉ đổi reference register).

## Related Code Files
- Modify: `prompts/prompt-expander-image.md`, `prompts/prompt-expander-video.md`,
  `references/visual-prompt-template.md`, `references/genre-keywords.md`,
  `references/negative-lists.md`, `prompts/music-prompt-builder.md`,
  `references/music-mood-mapping.md`

## Implementation Steps
1. `negative-lists.md`: cấu trúc 4 layer 10+5+5+4=24 (đổi "Max 20"→"Max 24"); thêm
   hướng dẫn lấy Layer 4 từ active-style; sửa Composed Example.
2. `prompt-expander-image.md`: thêm bước load active-style; sửa Step 7 + self-check
   #4 + thêm self-check Layer 4 negative.
3. `prompt-expander-video.md`: thêm load active-style; sửa self-check #7 + Style &
   Ambiance dùng Style block.
4. `visual-prompt-template.md`: sửa Style spec + rule cinema reference; annotate
   example là của painterly-realism.
5. `genre-keywords.md`: đổi 5 dòng "Style anchor" → "Default recommended style".
6. Music decouple: sửa `music-prompt-builder.md` (đọc music/score anchor) +
   `music-mood-mapping.md` (Base style → default genre + override bằng anchor).
7. Regression check: chạy thử `--style painterly-realism-cinematic` trên fixture,
   so Style section với output v0.2 (tinh thần khớp).

<!-- Updated: Validation Session 1 - cap 24 not 20 (Q3); music decouple +2 files (Q4) -->

## Success Criteria
- [ ] Không còn "Crouching Tiger"/"Hero" như quy tắc BẮT BUỘC toàn cục trong
      expander/template/genre-keywords (chỉ còn trong entry painterly-realism +
      example annotated + làm music/score anchor mặc định của vài style).
- [ ] Image/video expander đọc `.work/active-style.md` cho Style + negatives.
- [ ] Negative đúng 24 item (10+5+5+4).
- [ ] `--style painterly-realism-cinematic` reproduce tinh thần output v0.2.
- [ ] Đổi sang `--style donghua-xianxia` → Style section + negatives đổi theo.
- [ ] Music prompt đọc music/score anchor của style (không hardcode Crouching Tiger).

## Risk Assessment
- Style accent phá identity anchor → đã cảnh báo ở recommend (Phase 2); expander
  vẫn paste anchor verbatim, chỉ render khác.
- Bỏ sót 1 chỗ hardcode → grep "Crouching Tiger\|Hero (2002)" toàn repo sau khi sửa.
