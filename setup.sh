#!/bin/bash
# visual-prompt — Antigravity, Codex CLI, and Claude Code installer (Linux + macOS)
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="visual-prompt"
CODEX_CONFIG_DIR="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_CONFIG_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENT_SKILLS_DIR="$HOME/.agents/skills"

link_path() {
    local target="$1"
    local source="$2"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        echo "ERROR: target exists and is not a symlink: $target"
        echo "       Move it manually, then re-run setup.sh."
        exit 1
    fi
    ln -sfn "$source" "$target"
}

echo "================================"
echo " visual-prompt setup"
echo " repo: $REPO"
echo "================================"

# 1. Python check
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi
echo "[OK] $(python3 --version)"

# 2. Create target dirs
mkdir -p "$HOME/.gemini/extensions"
mkdir -p "$HOME/.gemini/commands"
mkdir -p "$HOME/.gemini/antigravity-cli/plugins"
mkdir -p "$AGENT_SKILLS_DIR" "$CODEX_CONFIG_DIR/prompts"
mkdir -p "$CLAUDE_CONFIG_DIR/skills"

# 3. Agy links (the extension keeps its canonical repository layout).
link_path "$HOME/.gemini/extensions/$SKILL_NAME" "$REPO"
link_path "$HOME/.gemini/commands/$SKILL_NAME.toml" "$REPO/commands/$SKILL_NAME.toml"
link_path "$HOME/.gemini/antigravity-cli/plugins/$SKILL_NAME" "$REPO"

echo "[OK] Symlinks created:"
echo "     ~/.gemini/extensions/$SKILL_NAME           -> $REPO"
echo "     ~/.gemini/commands/$SKILL_NAME.toml         -> $REPO/commands/$SKILL_NAME.toml"
echo "     ~/.gemini/antigravity-cli/plugins/$SKILL_NAME -> $REPO"

# 4. Codex links: native skill + explicit custom-prompt slash shim.
link_path "$AGENT_SKILLS_DIR/$SKILL_NAME" \
    "$REPO/adapters/codex/$SKILL_NAME"
link_path "$CODEX_CONFIG_DIR/prompts/$SKILL_NAME.md" \
    "$REPO/adapters/codex/$SKILL_NAME.md"
echo "     $AGENT_SKILLS_DIR/$SKILL_NAME -> $REPO/adapters/codex/$SKILL_NAME"
echo "     $CODEX_CONFIG_DIR/prompts/$SKILL_NAME.md -> $REPO/adapters/codex/$SKILL_NAME.md"

# 5. Claude Code link. Claude discovers SKILL.md beneath ~/.claude/skills.
link_path "$CLAUDE_CONFIG_DIR/skills/$SKILL_NAME" \
    "$REPO/adapters/claude-code/$SKILL_NAME"
echo "     $CLAUDE_CONFIG_DIR/skills/$SKILL_NAME -> $REPO/adapters/claude-code/$SKILL_NAME"

# 6. Plugin manifest (only create it when absent).
if [ ! -f "$REPO/plugin.json" ]; then
    printf '%s\n' '{"name": "visual-prompt"}' > "$REPO/plugin.json"
fi

echo ""
echo "[OK] Setup completed."
echo ""
echo "Test Agy: /visual-prompt <input.txt>"
echo "Test Codex native: \$visual-prompt <input.txt>"
echo "Test Codex slash shim: /prompts:visual-prompt <input.txt>"
echo "Test Claude Code: /visual-prompt <input.txt>"
echo "Default output: QA + image prompts. Add --video/--videos N and/or --music [N] explicitly."
