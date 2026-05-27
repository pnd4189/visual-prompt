---
phase: 1
title: "Style Catalog (web research 18 styles)"
status: done
priority: P1
effort: "1d"
dependencies: []
---

# Phase 1: Style Catalog (web research 18 styles)

## Overview

Web-research 18 art style cho văn học mạng TQ và viết `references/style-catalog.md`
— nguồn chân lý duy nhất về style. Schema entry ở đây = format của
`.work/active-style.md` (materialize ở Phase 2) nên phải chốt chính xác trước.

## Requirements
- Functional: 18 entry, mỗi entry đủ field schema dưới; mỗi entry có `Style block`
  EN paste-ready + `style negatives` + `reference anchors` verify được qua web.
- Non-functional: file < ~400 dòng vẫn ưu tiên đủ thông tin; id kebab-case ổn định
  (dùng làm giá trị `--style` và key cache).

## Architecture

### Entry schema (cố định — Phase 2/3 phụ thuộc)
```
### <id> — <Tên VN> / <EN name>
- category: narrative-safe | accent-title-card | video-oriented
- best-fit genres: <comma list trong {tiên hiệp, huyền huyễn, đô thị, cổ điển, võ hiệp}>
- description: <1-2 dòng thẩm mỹ>
- reference anchors: <artist / phim / donghua / game — web-verified, ghi năm nếu có>
- Style block (EN, paste-ready): <medium + render keywords + palette cue + "16:9 aspect ratio">
- palette: <tông màu chủ đạo>
- style negatives: <3-5 item, comma-separated, chống lệch style>
- music/score anchor: <1 dòng EN — register nhạc nền hợp style, vd "Tan Dun-style
  guzheng+erhu orchestral" / "synth-orchestral donghua hybrid" / "dark ambient
  ritual drone". Music-prompt-builder đọc field này (Phase 3, Q4 validation)>
- anchor consistency: tốt | khá | khó  (khả năng giữ identity anchor qua nhiều scene)
- image: yes|weak · video(8s): yes|weak
```
`.work/active-style.md` = COPY nguyên 1 entry này (Phase 2 materialize).

### 18 id + phân loại (chốt)
narrative-safe (10): `donghua-xianxia`, `painterly-realism-cinematic`,
`semi-realistic-digital-painting`, `light-novel-moe`, `concept-art-cityscape`,
`dark-fantasy-modao`, `game-cg-25d`, `dark-zhiguai-folk-horror`,
`scifi-donghua-kehuan`, `manhua`.
accent-title-card (7): `ink-wash-stylized`, `flat-poster-silhouette`,
`traditional-pattern-minimal`, `watercolor-gouache`,
`minimalist-calligraphy-symbolic`, `folk-nianhua`, `photobash-epic-poster`.
video-oriented (1): `ink-wash-animation`.

`painterly-realism-cinematic` = chính style cinematic 4K hiện tại → Style block của
nó PHẢI reproduce được output cũ (Crouching Tiger 2000 / Hero 2002 vẫn là reference
anchor của riêng entry này, không còn là quy tắc toàn cục).

## Related Code Files
- Create: `references/style-catalog.md`

## Implementation Steps
1. Với mỗi trong 18 style: WebSearch để xác định reference works thật (artist /
   donghua / phim / game tiêu biểu) + thuật ngữ render chuẩn. Ghi anchor verify được.
2. Viết entry theo schema trên. `painterly-realism-cinematic` viết trước, đối chiếu
   `references/visual-prompt-template.md` (IMAGE EXAMPLE) để Style block trùng tinh
   thần output v0.2.
3. Mỗi entry tự soạn `style negatives` (3-5) đặc thù (vd ink-wash: "no photographic
   detail, no 3D render, no hard CGI edges"; donghua: "no muted desaturation, no
   live-action realism").
4. Gắn `anchor consistency` trung thực: accent/video → khó; ghi rõ.
5. Thêm phần đầu file: bảng tra nhanh id→category + 1 dòng mô tả (để recommender và
   error message liệt kê id).

<!-- Updated: Validation Session 1 - +music/score anchor field (Q4) -->

## Success Criteria
- [ ] `references/style-catalog.md` có đủ 18 entry, mỗi entry đủ 10 field schema (gồm music/score anchor).
- [ ] Mỗi `reference anchors` có ít nhất 1 tác phẩm/nghệ sĩ thật (web-verified).
- [ ] `painterly-realism-cinematic` Style block đối chiếu khớp tinh thần example cũ.
- [ ] Bảng tra nhanh id→category ở đầu file (18 dòng).
- [ ] Mọi id kebab-case, khớp danh sách trên (Phase 2 validate dựa vào đây).

## Risk Assessment
- Web research dài → time-box mỗi style ~3-5 phút search; ưu tiên 1-2 anchor chắc.
- Reference anchor lỗi thời → ghi năm + nguồn; tránh nghệ sĩ vô danh không verify được.
