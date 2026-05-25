# Antigravity Integration — visual-prompt

Skill này nạp vào Antigravity (Gemini CLI) qua 3 symlink (Linux/Mac/Windows-Admin)
hoặc copy fallback (Windows non-admin).

- Quick install: chạy `setup.sh` (Linux/Mac) hoặc `setup.bat` (Windows) ở repo root
- Full guide: xem [INSTALL.md](INSTALL.md)
- User guide tiếng Việt: xem [../HUONG-DAN-SU-DUNG.md](../HUONG-DAN-SU-DUNG.md)

## Windows Caveat

Không có symlink quyền → mỗi lần update repo (git pull / sửa prompt files…)
phải chạy lại `setup.bat` để đồng bộ lại copy. Khuyến nghị bật Developer Mode
(Settings → For Developers → Developer Mode ON) để dùng symlink thật.

## Files Antigravity nạp

- `~/.gemini/extensions/visual-prompt/SKILL.md` — context file (loaded mỗi turn)
- `~/.gemini/commands/visual-prompt.toml` — slash command definition
- `~/.gemini/antigravity-cli/plugins/visual-prompt/` — plugin discovery

## Uninstall

```bash
rm -f ~/.gemini/extensions/visual-prompt
rm -f ~/.gemini/commands/visual-prompt.toml
rm -f ~/.gemini/antigravity-cli/plugins/visual-prompt
```

Bibles ở `~/.gemini/bibles/` được giữ lại.
