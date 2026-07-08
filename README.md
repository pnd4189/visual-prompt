# visual-prompt

Tạo prompt ảnh + video 4K cinematic, chi tiết cao từ file truyện tiên hiệp /
võ hiệp tiếng Việt để làm video audio YouTube trong Antigravity/Agy CLI.

## Cài đặt nhanh

**Linux / macOS:**
```bash
bash setup.sh
```

**Windows:** `setup.bat` (admin/Dev Mode) — xem [antigravity/INSTALL.md](antigravity/INSTALL.md).

## Dùng

```
/visual-prompt <input.txt>
```

Output: 4 file `_qa.txt`, `_image_prompts.txt`, `_video_prompts.txt`,
`_music_prompts.txt` cạnh file input. Mặc định tạo khoảng 120-150 image prompts
và tối thiểu 20 video prompts; dùng `--images` / `--videos` để override khi cần
chạy nhanh.

Trước QA, skill kiểm tra file hiện tại có nối tiếp file trước không: nếu file bắt
đầu Chương N, workflow tìm Chương N-1 trong các `.txt` / `_qa.txt` lân cận và so
đoạn cuối-trước với đoạn mở-hiện tại để tránh nhảy chương hoặc bỏ sót chương.

Spectacle mặc định: dựng cảnh giàu kịch tính — phong cảnh/map rộng, đông nhân vật
trong khung, combat, đấu pháp — và được dramatize vượt text trong giới hạn thể
loại/nhận diện/continuity. `--epic` bơm scale mạnh hơn; `--faithful` chuyển sang
chế độ trung thành text (không bịa combat). Hai cổng tự động loại cảnh trùng lặp +
block prompt nông rồi regen.

Music prompt luôn là nhạc nền không lời nhẹ nhàng, sâu lắng, cảm xúc, có màu sắc
tiên hiệp/kiếm hiệp; không tạo nhạc sôi động, trailer, battle score, hoặc dồn dập
lấn át giọng đọc. Mỗi block theo format ngắn gọn kiểu Chap 5: một paragraph
English prompt + một dòng `Tags:`, hướng tới loop nền liền mạch dài 2-3 phút.

## Hướng dẫn đầy đủ

[HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) — guide tiếng Việt từ A-Z.

## License

MIT.
