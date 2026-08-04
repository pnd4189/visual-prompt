# Report — vp-batch 0201→0300 PAUSED for resume

**Paused:** 2026-06-26 23:52 (user đi ngủ)
**Series:** binh-thien-sach-vo-toi (donghua-xianxia, music 4, Gemini 3.1 Pro High)
**Status:** **5/10 done**, file 6 đang giữa (gate FAIL re-run).

## Done (5) — gdrive `1. CHƯA QA` có `_image_prompts.txt`
| # | File | Chương | Note |
|---|------|--------|------|
| 1 | 0201_0210 | 201-210 | ghép 209-210 (dịch tay) |
| 2 | 0211_0220 | 211-220 | **image-only** (video bypass 3/3 → bỏ video) |
| 3 | 0221_0230 | 221-230 | ghép 229-230 (agy dịch) |
| 4 | 0231_0240 | 231-240 | deep |
| 5 | 0241_0250 | 241-250 | deep |

## Còn lại (5): 0251_0260, 0261_0270, 0271_0280, 0281_0290, 0291_0300
- **File 6 (0251_0260)**: gate FAIL, re-run lần 3 khi pause → mai resume sẽ chạy lại; nếu lại FAIL 3/3 → **ship image-only** (như file 2): chạy check_anchor_consistency + check_content_safety --fix trên image rồi copy image+qa+music về gdrive, bỏ video.
- File 7 (0261_0270): range đầy đủ (261-270), continuity OK.
- File 8-10: đã agy-dịch thêm chương thiếu (271,279 / 287 / 293,294), range đầy đủ, continuity PASS.

## Fixes đã làm session này (để không lặp)
1. **Gap 209-210** (file 1): dịch tay + ghép vào `0201_0210_vi.txt`.
2. **File 2 video bypass 3/3**: ship image-only (image deep + qa + music, bỏ video). User approve.
3. **Gap 229-231, 241, 271, 279, 287, 293, 294** (9 chương): **agy CLI dịch** (Gemini 3.1 Pro High, prompt `/tmp/vp-gap/translate_prompt.md`), merge vào 6 file vi đúng vị trí → range đầy đủ, continuity PASS. File `Bản sao của 0201_0210.txt` (raw tham khảo) đã move khỏi CHƯA QA → `/tmp/vp-gap/`.
4. Runaway `find /home/dung -name load_input.py` killed (file 2).
5. Guard pgrep self-match bug → dùng `ps -eo`.

## Lệnh resume (mai)
```bash
cd "/home/dung/VIBE_CODING/1. OTHERS/visual-prompt"
GD='/home/dung/cloud/gdrive/1. YOUTUBE AUDIO/BÌNH THIÊN SÁCH/BINH THIEN SACH - VO TOI/BẢN DỊCH/1. CHƯA QA'
nohup bash scripts/run-folder.sh "$GD" >> "$HOME/vp-batch-0201-0300.log" 2>&1 &
```
- run-folder tự skip 5 file done (check `_image_prompts.txt`), chạy tiếp file 6-10.
- Relaunch monitor 10 phút (ps-based guard, tránh pgrep self-match).
- `.vp-series.conf` (style donghua-xianxia) + `~/.gemini/bibles/binh-thien-sach-vo-toi.md` persistent qua reboot.

## Dữ liệu an toàn qua reboot
- Outputs gdrive (5 file) ✅. LOCAL_BASE `$HOME/.cache/vp-run-binh-thien-sach-vo-toi/` persistent (KHÔNG /tmp). conf + bibles persistent. `/tmp/vp-gap/` (translation temp) có thể mất nhưng đã merge xong → không cần.

## Unresolved
- File 6 có thể lại gate FAIL 3/3 → ship image-only.
- Chương 209-210, 229-230 không có prompt riêng (file 1,3 done→skip, chỉ phục vụ continuity). Muốn prompt thì xóa output file đó re-gen.
