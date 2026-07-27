# Antigravity Integration — visual-prompt

Skill này nạp vào Antigravity (Gemini CLI), Codex CLI, và Claude Code qua symlink
riêng cho từng CLI (hoặc copy fallback trên Windows).

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

## Codex và Claude Code

- Codex native: `~/.agents/skills/visual-prompt` → `adapters/codex/visual-prompt`
- Codex slash shim: `~/.codex/prompts/visual-prompt.md` →
  `adapters/codex/visual-prompt.md`, gọi `/prompts:visual-prompt`
- Claude Code: `~/.claude/skills/visual-prompt` →
  `adapters/claude-code/visual-prompt`, gọi `/visual-prompt`

Các adapter chỉ là entrypoint; chúng đọc cùng canonical `commands/`, `prompts/`,
`references/`, `scripts/`, nên không có bản workflow bị lệch.

## Uninstall

```bash
rm -f ~/.gemini/extensions/visual-prompt
rm -f ~/.gemini/commands/visual-prompt.toml
rm -f ~/.gemini/antigravity-cli/plugins/visual-prompt
rm -f ~/.agents/skills/visual-prompt ~/.codex/prompts/visual-prompt.md
rm -f ~/.claude/skills/visual-prompt
```

Bibles ở `~/.gemini/bibles/` được giữ lại.
