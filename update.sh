#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  flutterff — update.sh
#  Run this whenever you edit flutterff.py
#  to push changes to ~/.local/bin
# ─────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
INSTALL_PATH="$INSTALL_DIR/flutterff"
SOURCE_PATH="$SCRIPT_DIR/flutterff.py"

GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
RED="\033[91m"
RESET="\033[0m"
BOLD="\033[1m"

echo ""
echo -e "${BOLD}${CYAN}🦊 flutterff — update${RESET}"
echo ""

# ── check source exists ───────────────────────
if [ ! -f "$SOURCE_PATH" ]; then
    echo -e "${RED}flutterff.py not found at:${RESET} $SOURCE_PATH"
    echo "Make sure you run update.sh from the same folder as flutterff.py"
    exit 1
fi

# ── check already installed ───────────────────
if [ ! -f "$INSTALL_PATH" ]; then
    echo -e "${YELLOW}flutterff not installed yet. Run setup.sh first.${RESET}"
    echo ""
    echo "  bash setup.sh"
    exit 1
fi

# ── show version diff ─────────────────────────
OLD_VER=$(grep -m1 'VERSION = ' "$INSTALL_PATH" | tr -d ' ' | cut -d'"' -f2 2>/dev/null || echo "unknown")
NEW_VER=$(grep -m1 'VERSION = ' "$SOURCE_PATH"  | tr -d ' ' | cut -d'"' -f2 2>/dev/null || echo "unknown")

echo -e "${YELLOW}Current version:${RESET} $OLD_VER"
echo -e "${YELLOW}New version:${RESET}     $NEW_VER"
echo ""

# ── backup old version ────────────────────────
BACKUP_PATH="$INSTALL_DIR/flutterff.bak"
cp "$INSTALL_PATH" "$BACKUP_PATH"
echo -e "${GREEN}✔ Backup saved:${RESET} $BACKUP_PATH"

# ── copy updated script ───────────────────────
cp "$SOURCE_PATH" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"
echo -e "${GREEN}✔ Updated:${RESET} $INSTALL_PATH"

# ── pre-warm uv cache ─────────────────────────
echo -e "${YELLOW}Re-warming uv cache...${RESET}"
uv run --script "$INSTALL_PATH" --version 2>/dev/null \
    && echo -e "${GREEN}✔ uv cache ready${RESET}" \
    || echo -e "${YELLOW}⚠ Pre-warm skipped — will resolve on next run${RESET}"

echo ""
echo -e "${BOLD}${GREEN}✔ Update complete!${RESET}"
echo ""
echo -e "If something broke, restore backup with:"
echo -e "  ${CYAN}cp ~/.local/bin/flutterff.bak ~/.local/bin/flutterff${RESET}"
echo ""