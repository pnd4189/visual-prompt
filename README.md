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

Đa dạng cảnh theo nội dung: pipeline đo mật độ hành động của truyện rồi đặt tỉ lệ
cảnh thực tế (truyện đối thoại không bị ép quota combat; đa dạng đến từ góc máy /
nhóm nhân vật / chi tiết). Hai cổng tự động loại cảnh trùng lặp + block prompt
nông rồi regen. Thêm `--epic` để bơm quy mô khi truyện hợp.

## Hướng dẫn đầy đủ

[HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) — guide tiếng Việt từ A-Z.

## License

MIT.
