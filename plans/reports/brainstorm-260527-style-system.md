# Brainstorm — Style System cho visual-prompt skill

Date: 2026-05-27 · Status: approved, ready for /ck:plan

## Problem

Skill hiện hardcode 1 style duy nhất: "cinematic 4K + painterly realism" neo bắt
buộc vào phim Crouching Tiger Hidden Dragon (2000) / Hero (2002). Văn học mạng TQ
đa dạng (donghua, thủy mặc, manhua, dark fantasy ma đạo, game CG, sci-fi
kehuan...) → cần hệ thống chọn style: recommend theo genre + cho user tự chọn,
áp dụng nhất quán cho toàn bộ image+video của 1 run.

## Requirements (chốt với user)

- Output: catalog 18 style (web-researched) + bảng gợi ý genre→style + bước
  recommend tương tác + flag `--style` + gỡ hardcode Crouching Tiger.
- Acceptance: no-flag → sau genre detect hiện recommend + alternatives + HỎI user
  chọn → toàn scene dùng style đó; `--style <id>` → bỏ qua hỏi; đổi `--style`
  re-run → scene regenerate (cache bust); `--style` sai → lỗi VN liệt kê id hợp lệ.
- Out of scope: không đụng QA/bible/music/TTS; 1 style/run; chỉ xuất text prompt;
  không thêm genre / không mở đam mỹ-ngôn tình.
- Constraints: LLM-loop + Python chỉ I/O; identity anchor verbatim giữ nguyên;
  16:9; string user = VN, prompt = EN.

## User decisions (locked)

1. Cơ chế chọn = **tương tác**: recommend rồi hỏi (STEP 3.5), `--style` skip hỏi.
2. Genre×Style = **tách hoàn toàn** (recommend mềm, mọi style cho mọi genre).
3. Catalog = **giữ đủ 18 + phân loại** (narrative-safe / accent-title-card / video).
4. Research = **web research từng style** (verify tên artist/phim/donghua thật).
5. Threading = **B (materialize `.work/active-style.md`)** — khớp pattern hash sẵn có.

## Architecture

### File mới
- `references/style-catalog.md` — 18 entry. Schema: id, category, best-fit genres,
  description, reference anchors (web-verified), Style block (paste-ready EN),
  palette, style negatives (3-5), anchor note, image/video suitability.
- `references/genre-style-recommendation.md` — bảng gợi ý mềm 5 genre → #1 +
  alternatives + lý do.
- `prompts/style-recommender.md` — LLM prompt: input genre (+ sample) → output
  recommend #1 + 2-3 alternatives + cảnh báo anchor cho style accent/video.

### 18 style → id + phân loại
Narrative-safe (10): donghua-xianxia, painterly-realism-cinematic,
semi-realistic-digital-painting, light-novel-moe, concept-art-cityscape,
dark-fantasy-modao, game-cg-25d, dark-zhiguai-folk-horror, scifi-donghua-kehuan,
manhua.
Accent/title-card (7): ink-wash-stylized, flat-poster-silhouette,
traditional-pattern-minimal, watercolor-gouache, minimalist-calligraphy-symbolic,
folk-nianhua, photobash-epic-poster.
Video-oriented (1): ink-wash-animation.

`painterly-realism-cinematic` = style cinematic 4K hiện tại → trở thành 1 trong 18
(default cho cổ điển/võ hiệp). Không phá hành vi cũ nếu user chọn nó.

### Genre→style recommend (mềm)
- tiên hiệp → donghua-xianxia (alt: painterly-realism-cinematic, game-cg-25d, ink-wash-stylized)
- huyền huyễn → dark-fantasy-modao (alt: game-cg-25d, concept-art-cityscape, donghua-xianxia)
- đô thị → semi-realistic-digital-painting (alt: manhua, scifi-donghua-kehuan)
- cổ điển → painterly-realism-cinematic (alt: watercolor-gouache, ink-wash-stylized)
- võ hiệp → painterly-realism-cinematic (alt: ink-wash-stylized, manhua)

### Pipeline change (commands/visual-prompt.toml)
- STEP 0: thêm flag `--style ([a-z0-9-]+)` → validate id ∈ catalog (sai → lỗi VN
  liệt kê id hợp lệ).
- STEP 3.5 (mới) STYLE RECOMMEND + CONFIRM: nếu `--style` set → skip hỏi; else load
  style-recommender → in recommend + alternatives + cảnh báo → hỏi user (Enter = #1).
  Materialize entry đã chọn → `.work/active-style.md`. Tính `style_hash` →
  `.work/style.hash`.
- STEP 6 cache key: `sha1(qa_hash + bible_hash + plan_hash + style_hash + scene_row)`
  → đổi style auto regenerate scene.

### Gỡ hardcode (breaking)
- prompt-expander-image self-check #4, prompt-expander-video self-check #7,
  visual-prompt-template Style spec: "cite Crouching Tiger/Hero" → "cite reference
  anchor của style đang chọn" (đọc `.work/active-style.md`).
- genre-keywords "Style anchor" mỗi genre → con trỏ default recommended style.

### Negative budget (giữ cap 20)
Tái cấu trúc: universal-core 6 + genre 4 + style 5 + AI-defense 5 = 20.
Style negatives lấy từ catalog entry.

## File change list
- Mới: references/style-catalog.md, references/genre-style-recommendation.md,
  prompts/style-recommender.md.
- Sửa: commands/visual-prompt.toml, prompts/prompt-expander-image.md,
  prompts/prompt-expander-video.md, references/visual-prompt-template.md,
  references/genre-keywords.md, references/negative-lists.md, SKILL.md,
  HUONG-DAN-SU-DUNG.md.

## Risks
1. Web research 18 style tốn thời gian (chốt làm, verify tên thật).
2. Style accent phá identity anchor → giảm thiểu = phân loại + cảnh báo lúc recommend.
3. Negative cap 20 chật → đã có phương án tái cấu trúc 6+4+5+5.
4. Bước hỏi tương tác giả định CLI foreground (đúng cách skill chạy).

## Success metrics
- 18 style trong catalog, mỗi style có reference anchor verify được + Style block
  paste-ready + style negatives.
- no-flag run hỏi style sau genre detect; `--style` skip; đổi style re-run regenerate.
- `painterly-realism-cinematic` reproduce đúng output cinematic 4K cũ.

## Next steps
- /ck:plan (default) lập kế hoạch implement theo file change list trên.
- Phase đầu nên là web research 18 style → viết style-catalog.md (heavy, gate các
  bước sau).

## Open questions
None.
