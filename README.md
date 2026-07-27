# visual-prompt

Tạo prompt ảnh 4K cinematic, grounded và chi tiết cao từ file truyện tiên hiệp /
võ hiệp tiếng Việt trong Antigravity/Agy, Codex CLI, hoặc Claude Code CLI.

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

Mặc định chỉ tạo 2 file `_qa.txt` và `_image_prompts.txt` cạnh file input. Thêm
`--video`/`--videos N` để bật video, `--music`/`--music N` để bật music; có thể
ghi mô tả rõ “tạo video prompt” hoặc “tạo music prompt” sau lệnh. `--no-video` và
`--no-music` luôn tắt medium tương ứng.

Trước QA, skill kiểm tra file hiện tại có nối tiếp file trước không: nếu file bắt
đầu Chương N, workflow tìm Chương N-1 trong các `.txt` / `_qa.txt` lân cận và so
đoạn cuối-trước với đoạn mở-hiện tại để tránh nhảy chương hoặc bỏ sót chương.

Mặc định grounded: mỗi scene có `source_anchor` nguyên văn từ đúng chapter.
Active parent model tự viết từng scene theo micro-batch tối đa 3; không subagent,
không parallel generation, không script sinh hàng loạt. Validator fail-closed
nếu anchor/nhân vật sai nguồn hoặc setting/camera/action/palette bị lặp.
Character bible cũng không được “hoàn thiện ngoại hình” bằng suy đoán: tuổi,
tóc, mặt, trang phục hoặc đạo cụ không có trong truyện phải giữ `not stated`.

Khi bật music, prompt luôn là nhạc nền không lời nhẹ nhàng, sâu lắng, cảm xúc, có màu sắc
tiên hiệp/kiếm hiệp; không tạo nhạc sôi động, trailer, battle score, hoặc dồn dập
lấn át giọng đọc. Mỗi block theo format ngắn gọn kiểu Chap 5: một paragraph
English prompt + một dòng `Tags:`, hướng tới loop nền liền mạch dài 2-3 phút.

## Hướng dẫn đầy đủ

[HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) — guide tiếng Việt từ A-Z.

## Dùng trên ba CLI

- Agy: `bash setup.sh`, sau đó `/visual-prompt ...`.
- Codex: installer symlink `~/.agents/skills/visual-prompt` (native
  `$visual-prompt`) và `~/.codex/prompts/visual-prompt.md` (slash
  `/prompts:visual-prompt`).
- Claude Code: installer symlink `~/.claude/skills/visual-prompt`, gọi trực tiếp
  `/visual-prompt ...`.

Symlink giữ một canonical workflow nên cập nhật repo là đủ. Nếu Windows không có
quyền symlink, installer dùng bản copy; chạy lại installer sau mỗi lần cập nhật.

## License

MIT.
