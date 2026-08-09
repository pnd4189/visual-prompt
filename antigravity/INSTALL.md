# Antigravity Install Guide — visual-prompt

Skill này nạp vào Antigravity (Gemini CLI), Codex CLI, và Claude Code qua các
symlink adapter.

## Linux / macOS

```bash
cd /path/to/visual-prompt
bash setup.sh
```

`setup.sh` tạo 3 symlink:
- `~/.gemini/extensions/visual-prompt` → repo
- `~/.gemini/commands/visual-prompt.toml` → `<repo>/commands/visual-prompt.toml`
- `~/.gemini/antigravity-cli/plugins/visual-prompt` → repo

Setup cũng merge named runtime guard `visual-prompt-active-model-guard` vào
`~/.gemini/config/hooks.json`; mọi hook khác trong file được giữ nguyên. Lớp này
buộc active Agy model tự ghi từng scene và chặn subagent/runtime generator ngay
ở tool call. Installer tạo launcher ổn định
`~/.gemini/config/visual-prompt-active-model-guard.py` để Agy không làm vỡ path
repo có khoảng trắng. Chạy lại setup là idempotent.

Verify: mở Antigravity → gõ `/visual-prompt` → autocomplete xuất hiện.

Đồng thời setup tạo:

- `~/.agents/skills/visual-prompt` → adapter Codex native (`$visual-prompt`)
- `~/.codex/prompts/visual-prompt.md` → slash shim (`/prompts:visual-prompt`)
- `~/.claude/skills/visual-prompt` → adapter Claude (`/visual-prompt`)

Codex native là đường chạy khuyến nghị; slash shim chỉ chuyển nguyên arguments.
Claude adapter tắt model auto-invocation để tránh chạy ngoài ý muốn.

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
5. Cài Agy guard:
   `python3 <repo>/scripts/install_agy_guard.py --repo-root <repo> --target ~/.gemini/config/hooks.json`
6. Codex: symlink `<repo>/adapters/codex/visual-prompt` vào
   `~/.agents/skills/visual-prompt` và `<repo>/adapters/codex/visual-prompt.md`
   vào `~/.codex/prompts/visual-prompt.md`
7. Claude Code: symlink `<repo>/adapters/claude-code/visual-prompt` vào
   `~/.claude/skills/visual-prompt`

## Uninstall

```bash
rm -f ~/.gemini/extensions/visual-prompt
rm -f ~/.gemini/commands/visual-prompt.toml
rm -f ~/.gemini/antigravity-cli/plugins/visual-prompt
rm -f ~/.agents/skills/visual-prompt ~/.codex/prompts/visual-prompt.md
rm -f ~/.claude/skills/visual-prompt
```

Bibles ở `~/.gemini/bibles/` được giữ lại (chứa data của user).
Vì `hooks.json` có thể chứa hook khác, uninstall không xoá cả file; nếu muốn gỡ
guard, xoá key `visual-prompt-active-model-guard` trong JSON đó và file launcher
`~/.gemini/config/visual-prompt-active-model-guard.py`.
