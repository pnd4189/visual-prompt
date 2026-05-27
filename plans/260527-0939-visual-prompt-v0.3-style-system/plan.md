---
title: "Visual Prompt v0.3 — Multi-Style System"
description: "Add a selectable art-style system (18 web-researched styles) to /visual-prompt: recommend a style per genre after detect, let user pick (interactive or --style flag), thread chosen style through all image+video prompts, remove the hardcoded Crouching-Tiger cinematic anchor"
status: implemented
priority: P2
branch: "main"
tags: [skill, antigravity, llm-driven, style, xianxia, prompts]
blockedBy: []
blocks: []
created: "2026-05-27T02:39:23.775Z"
createdBy: "ck:plan"
source: skill
---

# Visual Prompt v0.3 — Multi-Style System

## Overview

Skill hiện hardcode 1 style ("cinematic 4K + painterly realism", neo bắt buộc vào
Crouching Tiger Hidden Dragon / Hero). v0.3 thêm hệ thống chọn style đa dạng cho
văn học mạng TQ: catalog 18 style (web-researched), bước recommend style tương tác
sau genre detect, flag `--style <id>` để chọn thủ công, thread style đã chọn vào
mọi image+video prompt một cách nhất quán. Genre và style **tách rời** (recommend
mềm — mọi style chọn được cho mọi genre).

Nguồn yêu cầu: `plans/reports/brainstorm-260527-style-system.md` (đã duyệt).

## Key design decisions (locked in brainstorm)

- **Chọn style = tương tác**: STEP 3.5 recommend + hỏi user; `--style` skip hỏi.
- **Genre×Style tách hoàn toàn** (recommend mềm).
- **Giữ đủ 18 style + phân loại** narrative-safe (10) / accent-title-card (7) / video (1).
- **Web research từng style** (verify reference anchor thật).
- **Threading = materialize** `.work/active-style.md` + `style_hash` vào scene cache key.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Style Catalog (web research 18 styles)](./phase-01-style-catalog-web-research-18-styles.md) | Done |
| 2 | [Recommendation + Selection + Pipeline](./phase-02-recommendation-selection-pipeline.md) | Done |
| 3 | [Decouple Expanders + References](./phase-03-decouple-expanders-references.md) | Done |
| 4 | [Docs](./phase-04-docs.md) | Done |

Dependency chain: P1 → P2 → P3 → P4 (linear). P1 định nghĩa schema entry =
format của `.work/active-style.md`; P2 sinh ra file đó; P3 tiêu thụ nó.

## Dependencies

Builds on completed plans `260522-2230-...` (v0.1) và `260525-1305-...` (v0.2),
cả hai `status: implemented` — không block. Không có cross-plan dependency mới.

## Out of scope

Không đụng QA/bible/TTS logic và music segmentation/mood logic; 1 style/run
(không trộn style giữa scene); vẫn chỉ xuất text prompt; không thêm genre / không
mở đam mỹ-ngôn tình.
**Ngoại lệ (validation):** music *score anchor* (reference nhạc) được decouple theo
style đã chọn — xem Validation Log Q4.

## Validation Log

### Session 1 — 2026-05-27

Verification (Standard tier): 8 file modify đều tồn tại; cache key tại
`commands/visual-prompt.toml:166`; negative cap 20; SKILL version 0.2.0. Failed: 0.

Quyết định:
- **Q1 default style (no --style):** dùng **bảng recommend #1** (đổi look so với
  v0.2 — vd tiên hiệp default = donghua-xianxia). Không giữ painterly làm default.
- **Q2 interactive:** CLI dừng-hỏi được; **fallback = recommend #1** khi headless/
  không trả lời (+ in cách override bằng --style).
- **Q3 negative cap:** **nới cap lên 24** (anti-Western 10 + genre 5 + AI 5 +
  style 4). KHÔNG rút anti-Western xuống 6.
- **Q4 music refs:** **decouple music score luôn** — style catalog thêm field
  `music/score anchor`; music-prompt-builder + music-mood-mapping đọc anchor đó
  thay vì hardcode Crouching Tiger. Music segmentation/mood logic giữ nguyên.

Propagated → Phase 1 (schema +music anchor), Phase 2 (default #1 + fallback),
Phase 3 (cap 24 + music decouple + 2 file nhạc), Phase 4 (docs note).

### Whole-Plan Consistency Sweep
Quét toàn plan: sửa 2 chỗ stale "cap 20 / 6+4+5+5" ở Phase 3 (Overview + step 1)
→ 24 / 10+5+5+4. "negative cap 20" ở Verification là mô tả state HIỆN TẠI của code
(đúng). Không còn mâu thuẫn chưa giải quyết. ✅
