# Antigravity Install Guide — visual-prompt

Skill này nạp vào Antigravity (Gemini CLI) qua 3 symlink.

## Linux / macOS

```bash
cd /path/to/visual-prompt
bash setup.sh
```

`setup.sh` tạo 3 symlink:
- `~/.gemini/extensions/visual-prompt` → repo
- `~/.gemini/commands/visual-prompt.toml` → `<repo>/commands/visual-prompt.toml`
- `~/.gemini/antigravity-cli/plugins/visual-prompt` → repo

Verify: mở Antigravity → gõ `/visual-prompt` → autocomplete xuất hiện.

## Windows (Admin / Developer Mode)

```cmd
cd C:\path\to\visual-prompt
setup.bat
```

Yêu cầu: PowerShell as Administrator HOẶC Windows 10/11 Developer Mode bật.
Script tự thử `mklink`. Nếu fail → fallback **copy** (xem dưới).

## Windows (Non-Admin — copy fallback)

`setup.bat` tự fallback sang `xcopy` nếu symlink fail. Khi đó:
- Mỗi lần cập nhật repo (git pull, sửa prompt files…) → **chạy lại `setup.bat`**
  để đồng bộ. Không có symlink nên copy bị stale.

## Manual install (mọi OS)

Nếu setup scripts không chạy được:

1. `mkdir -p ~/.gemini/extensions ~/.gemini/commands ~/.gemini/antigravity-cli/plugins`
2. Symlink (hoặc copy) `<repo>` vào `~/.gemini/extensions/visual-prompt`
3. Symlink (hoặc copy) `<repo>/commands/visual-prompt.toml` vào
   `~/.gemini/commands/visual-prompt.toml`
4. Symlink (hoặc copy) `<repo>` vào `~/.gemini/antigravity-cli/plugins/visual-prompt`

## Uninstall

```bash
rm -f ~/.gemini/extensions/visual-prompt
rm -f ~/.gemini/commands/visual-prompt.toml
rm -f ~/.gemini/antigravity-cli/plugins/visual-prompt
```

Bibles ở `~/.gemini/bibles/` được giữ lại (chứa data của user).
