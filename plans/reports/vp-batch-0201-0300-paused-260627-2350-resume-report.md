# Report — vp-batch 0201→0300 PAUSED (regen phase) for resume

**Paused:** 2026-06-27 23:50 (user đi ngủ, lần 2)
**Status:** **8/10 done + quality-fixed**, file 1 + file 9 đang regen (outputs đã delete, chờ re-pipeline).

## Done 8/10 (quality-fixed ✅)
| File | Chương | Note |
|-----|--------|------|
| 2 (0211_0220) | 211-220 | image-only; fixed dedup 4 + None 96 |
| 3 (0221_0230) | 221-230 | PASS |
| 4 (0231_0240) | 231-240 | PASS |
| 5 (0241_0250) | 241-250 | Negative diverse 150/150 OK |
| 6 (0251_0260) | 251-260 | PASS |
| 7 (0261_0270) | 261-270 | image-only; fixed Iron策→Thiết Sách |
| 8 (0271_0280) | 271-280 | image-only; fixed dedup 22 + None 4 |
| 10 (0291_0300) | 291-300 | fixed None 25 |

## Cần regen (outputs ĐÃ DELETE trên gdrive)
- **File 1 (0201_0210)**: Opus đánh template v1 cũ (Style 1/149, Camera 4/149, Setting 5/149, "None" 52, build-dup 90). Cần re-pipeline ra v2/v3 diverse.
- **File 9 (0281_0290)**: pipeline fallback (Style 1/150, Camera 1/150, Setting 1/150, spam đã strip nhưng diversity vẫn cực thấp). Cần re-pipeline.

## Quality review đã xong
- **Opus review** (Claude Opus 4.6): `plans/reports/vp-batch-opus-quality-review-260627.md` (12KB, chi tiết per-file + root-cause).
- **My deterministic review**: 150 scenes/file, 10-section, 0 shallow, 0 boiler/Hanzi (sau fix), anchor ✓ all, safety ✓ (file 5/10 religion WARN-only 'desecrated' — chấp nhận bối cảnh chiến tranh tôn giáo).

## Resume (mai)
```bash
cd "/home/dung/VIBE_CODING/1. OTHERS/visual-prompt"
GD='/home/dung/cloud/gdrive/1. YOUTUBE AUDIO/BÌNH THIÊN SÁCH/BINH THIEN SACH - VO TOI/BẢN DỊCH/1. CHƯA QA'
nohup bash scripts/run-folder.sh "$GD" >> "$HOME/vp-batch-0201-0300.log" 2>&1 &
```
- run-folder skip 8 done, **regen file 1 + file 9** (gdrive _image_prompts đã delete).
- File 1 regen hay flaky (thiếu output 3 lần tối nay) — nếu lại fail: restart lại / assemble từ scene nếu có / chấp nhận.
- Sau khi 1+9 done → **re-review diversity** (Style/Camera/Setting uniq) → nếu OK → final report.

## Lưu ý quan trọng (root-cause từ Opus)
- "None" literal trong Subject (template bug): 247× — đã clean keeper files.
- "X X" duplication (build/hair): 119× — đã clean keeper files.
- 3 pipeline version (v1 boilerplate / v2 lens / v3 bracket): file 1=v1, file 9=fallback → regen.
- 4 file image-only (2,7,8,9): video bypass (gate FAIL video 3/3, image deep). File 9 regen có thể ra video nếu deep.

## Dữ liệu an toàn qua reboot
- 8 outputs gdrive ✅. Opus review plans/reports/ ✅. LOCAL_BASE `$HOME/.cache` persistent. `/tmp/vp-gap/` (review temp, my fix scripts) có thể mất — đã copy Opus review ra plans/reports/, không cần nữa.
