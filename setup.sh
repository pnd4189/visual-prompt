#!/bin/bash
# visual-prompt — Antigravity / Gemini CLI installer (Linux + macOS)
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="visual-prompt"

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

# 3. Three symlinks (verified pattern from cli-tran skill)
ln -sfn "$REPO" "$HOME/.gemini/extensions/$SKILL_NAME"
ln -sf  "$REPO/commands/$SKILL_NAME.toml" "$HOME/.gemini/commands/$SKILL_NAME.toml"
ln -sfn "$REPO" "$HOME/.gemini/antigravity-cli/plugins/$SKILL_NAME"

echo "[OK] Symlinks created:"
echo "     ~/.gemini/extensions/$SKILL_NAME           -> $REPO"
echo "     ~/.gemini/commands/$SKILL_NAME.toml         -> $REPO/commands/$SKILL_NAME.toml"
echo "     ~/.gemini/antigravity-cli/plugins/$SKILL_NAME -> $REPO"

# 4. Inner skill mirror (skill discovery convention)
mkdir -p "$REPO/skills/$SKILL_NAME"
ln -sfn "$REPO/SKILL.md" "$REPO/skills/$SKILL_NAME/SKILL.md"

# 5. Plugin manifest
if [ ! -f "$REPO/plugin.json" ]; then
    cat > "$REPO/plugin.json" <<'EOF'
{"name": "visual-prompt"}
EOF
fi

echo ""
echo "[OK] Setup completed."
echo ""
echo "Test: mở Antigravity, gõ /visual-prompt → autocomplete xuất hiện."
echo "Usage: /visual-prompt <input.txt> [--series NAME] [--genre NAME] [--images N] [--videos M] [--force-redo]"
