---
type: brainstorm-report
date: 2026-06-22 13:23
skill: visual-prompt
topic: Content-Safety Gate (copyright + policy-safe visual prompts)
status: approved-pending-plan
---

# Brainstorm — Content-Safety Gate cho /visual-prompt

## Problem
Skill `/visual-prompt` sinh image/video/music prompt từ truyện tiên/võ hiệp. Cần
cơ chế **bổ sung yêu cầu** để prompt KHÔNG: mô phỏng nhãn hiệu/logo thương hiệu,
người nổi tiếng/khuôn mặt thật, nhân vật IP có bản quyền, ảnh có bản quyền; KHÔNG
mô tả máu me/bạo lực quá mức, nội dung tình dục/hở hang; KHÔNG bịa đặt/xuyên
tạc/xúc phạm tôn giáo. Mục tiêu: tránh vi phạm bản quyền + an toàn nền tảng
(YouTube) + nhạy cảm thị trường.

## Hiện trạng (scout)
- Đã có cơ chế copyright-safe **dạng MỀM**: `negative-lists.md` Layer 4 (4 mục:
  `no copied web image, no celebrity face, no known-character likeness, no exact
  branded costume`); self-check trong 2 expander; "Original outputs only" ở
  SKILL.md + template.
- Tầng enforce cứng = `validate_artifacts.py` + 3 gate TOML (plan gate STEP 5.5,
  depth gate STEP 7, self-audit STEP 8) — **chỉ kiểm cấu trúc, không quét nội
  dung** prompt để bắt brand/tên người.
- Tiền lệ gate quét nội dung: `scripts/check_anchor_consistency.py` (regex scan +
  `--fix`, exit 0/2/1) — **chỉ wired trong `run-folder.sh` (batch), CHƯA có trong
  TOML single-run**.

## Lỗ hổng
1. Tên brand/trademark trong prompt DƯƠNG (negative `no logo` không chặn).
2. Tên người nổi tiếng/mặt thật (rủi ro cao nhất với xianxia/wuxia).
3. Likeness nhân vật IP (1 mục mềm, dễ bị bỏ qua).
4. Gore/bạo lực quá mức; 5. Nội dung tình dục/hở hang; 6. Xúc phạm/xuyên tạc tôn
   giáo — CHƯA có rule nào.
7. Không có "bắt cứng" — phụ thuộc model tuân thủ (memory ghi nhận Agy hay bỏ qua
   rule mềm).

## Approaches đã cân nhắc
| | Mô tả | Pro | Con |
|--|--|--|--|
| A | Chỉ siết rule mềm | Rẻ, nhanh | Dễ bị model phớt lờ |
| B | Chỉ thêm gate cứng | Bắt được vi phạm | Sinh "mù" rồi lọc; thiếu phòng ngừa |
| **C (chọn)** | **Hybrid mềm + gate cứng** | Vá đủ; khớp "enforced not suggested" | Tốn công hơn (1 script + 1 data + wiring) |

## Quyết định (user-approved)
- **Enforce**: Hybrid (mềm + gate cứng).
- **On-violation**: Auto-strip + WARN (không chặn batch headless).
- **7 nhóm chặn**: (1) brand/logo/trademark, (2) người nổi tiếng/mặt thật,
  (3) nhân vật IP bản quyền, (4) ảnh/tác phẩm bản quyền, (5) gore/bạo lực quá
  mức, (6) tình dục/nudity/hở hang, (7) xúc phạm/xuyên tạc/bịa đặt tôn giáo.

## Trade-off rails (đã chốt)
- **Spectacle vs gore**: GIỮ combat/đấu pháp (đúng triết lý spectacle); CHỈ chặn
  gore quá mức (chặt đầu, moi ruột, máu phun, tra tấn). Combat stylized/ít máu OK.
- **False-positive likeness**: pattern likeness CHỈ kích hoạt khi có trigger
  ("looks like / in the style of / cosplay / giống / theo phong cách" + Tên
  riêng) — KHÔNG quét trần mọi Proper Noun (tránh xoá nhầm tên nhân vật Hán-Việt).
- **Tôn giáo (sắc thái)**: genre vốn mang yếu tố Đạo/Phật (tu tiên, đạo sĩ, chùa)
  — KHÔNG chặn hình tu tiên hư cấu. CHỈ chặn xúc phạm/xuyên tạc/báng bổ tôn giáo
  THẬT (vẽ tiên tri/thần linh có thật như cấm Muhammad trong Islam; ghép symbol
  thiêng với gore/nudity; bịa đặt giáo lý). Enforce chủ yếu rule mềm + blocklist
  token rủi ro cao → thiên WARN (regex khó phán ngữ cảnh).

## Giải pháp (kiến trúc 2 tầng)

### Tầng MỀM (text — phòng ngừa lúc sinh)
- `references/negative-lists.md`: Layer 4 đổi tên → "Safety & Compliance"; thêm
  token chủ chốt (no brand logo, no real public figure, no nudity, no graphic
  gore). **Re-budget cap 28** (giảm Layer 1 10→8 hoặc nâng cap — quyết ở plan).
- `prompts/prompt-expander-image.md` + `prompt-expander-video.md`: "Safety check"
  → rule cứng + thêm MANDATORY SELF-CHECK: cấm tên brand/người thật/IP ở MỌI
  section dương; cấm nudity/sexual; combat OK nhưng không gore; tôn trọng tôn
  giáo; nếu chương có nội dung cấm → trừu tượng hoá.
- `prompts/scene-planner.md`: rail cấp kế hoạch — không lên scene chỉ để khai
  thác gore/nhạy cảm/báng bổ.
- `references/visual-prompt-template.md`: cập nhật mục originality/safety.
- `SKILL.md` + `commands/visual-prompt.toml`: thêm RULE content-safety hạng nhất
  (như RULE 0) + mô tả gate ở STEP 7/8. Bump version 2 chỗ (SKILL.md +
  gemini-extension.json).

### Tầng CỨNG (deterministic gate — bắt sau khi sinh)
- **NEW `scripts/check_content_safety.py`** — mirror `check_anchor_consistency.py`:
  `--output --blocklist [--fix]`, exit 0/2/1, scan→fix→report, in WARN khi sửa.
- **NEW `references/blocklist-content-safety.md`** (data): brand list (global +
  TQ), IP franchise phổ biến, regex gore/sexual (song ngữ Anh-Việt), pattern
  likeness-trigger, token tôn giáo rủi ro cao.
- Auto-strip mapping: brand → bỏ từ; "looks like X" → bỏ mệnh đề; gore → "a
  fallen figure, no graphic blood"; nudity → "modestly clothed".
- **Wiring**: TOML STEP 7 (sau assemble, cạnh depth gate, `--fix`, trên
  `_image_prompts.txt` + `_video_prompts.txt`) + `run-folder.sh` (cạnh anchor
  gate ~L185) + STEP 8 self-audit chạy lại KHÔNG `--fix` → exit 0 = PASS, còn vi
  phạm = WARN.

## Files
- NEW (2): `scripts/check_content_safety.py`, `references/blocklist-content-safety.md`
- EDIT (9): `references/negative-lists.md`, `prompts/prompt-expander-image.md`,
  `prompts/prompt-expander-video.md`, `prompts/scene-planner.md`,
  `references/visual-prompt-template.md`, `SKILL.md`,
  `commands/visual-prompt.toml`, `scripts/run-folder.sh`, `gemini-extension.json`

## Acceptance
- Prompt output (image/video) không chứa tên brand/người thật/IP có trong
  blocklist; không có token gore/nudity quá mức; combat hư cấu vẫn giữ.
- `check_content_safety.py --fix` thay span vi phạm bằng generic, in WARN list.
- STEP 8 self-audit chạy gate không `--fix` → exit 0 (hoặc WARN nếu còn).
- Không xoá nhầm tên nhân vật Hán-Việt (likeness chỉ bắt khi có trigger).
- Hình tu tiên/đạo sĩ/chùa hư cấu KHÔNG bị chặn.

## Out of scope
- Không xây bộ phân loại ML; gate là blocklist + regex.
- Không bao phủ 100% brand/IP/tôn giáo thế giới (blocklist hữu hạn, có thể mở
  rộng dần).
- Không chặn combat/đấu pháp (giữ triết lý spectacle).

## Risks
- Blocklist không bao giờ đủ → bổ sung dần; rule mềm là lớp chính.
- Auto-strip có thể làm prompt hơi cụt nghĩa ở câu bị sửa → mapping generic phải
  tự nhiên.
- Re-budget negative cap 28 → cần test không vỡ depth gate (`negative < 20`).

## Unresolved (quyết ở plan)
- Re-budget cap 28: giảm Layer 1 (10→8) hay nâng cap tổng?
- Scan trên assembled `.txt` (như anchor) hay trên `.work/scene-*.md`? (đề xuất:
  `.txt`, khớp anchor gate + auto-strip 1 lần).
- Bump version: 0.8.0 → 0.9.0 hay 0.10.0?
