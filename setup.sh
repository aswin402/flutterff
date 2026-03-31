#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  flutterff — setup.sh
#  First time install. Run once.
# ─────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
INSTALL_PATH="$INSTALL_DIR/flutterff"

GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
RED="\033[91m"
RESET="\033[0m"
BOLD="\033[1m"

echo ""
echo -e "${BOLD}${CYAN}🦊 flutterff — setup${RESET}"
echo ""

# ── 1. check uv ───────────────────────────────
echo -e "${YELLOW}Checking uv...${RESET}"
if ! command -v uv &>/dev/null; then
    echo -e "${RED}uv not found!${RESET}"
    echo "Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo -e "${GREEN}✔ uv found:${RESET} $(which uv)"

# ── 2. check flutter ──────────────────────────
echo -e "${YELLOW}Checking flutter...${RESET}"
if ! command -v flutter &>/dev/null; then
    echo -e "${RED}flutter not found in PATH!${RESET}"
    echo "Make sure Flutter is installed and added to PATH."
    exit 1
fi
echo -e "${GREEN}✔ flutter found:${RESET} $(which flutter)"

# ── 3. check GTK WebKit (Linux) ───────────────
echo -e "${YELLOW}Checking WebKitGTK...${RESET}"

# Try 4.1 first (Ubuntu 22.04+/Debian 12+), then fall back to 4.0
_webkit_ok=false
python3 -c "import gi; gi.require_version('WebKit2', '4.1'); from gi.repository import WebKit2" 2>/dev/null && _webkit_ok=true
$_webkit_ok || python3 -c "import gi; gi.require_version('WebKit2', '4.0'); from gi.repository import WebKit2" 2>/dev/null && _webkit_ok=true

if ! $_webkit_ok; then
    echo -e "${YELLOW}WebKitGTK not found. Installing...${RESET}"
    if command -v apt &>/dev/null; then
        # Detect which webkit package is available (4.1 for Ubuntu 22.04+, 4.0 for older)
        if apt-cache show gir1.2-webkit2-4.1 &>/dev/null; then
            sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
        elif apt-cache show gir1.2-webkit2-4.0 &>/dev/null; then
            sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0
        else
            echo -e "${RED}Could not find a WebKit2 package.${RESET}"
            echo "Try:  sudo apt install python3-gi gir1.2-webkit2-4.1"
            exit 1
        fi
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-gobject webkit2gtk-4.1
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-gobject webkit2gtk4.1
    else
        echo -e "${RED}Could not auto-install WebKitGTK.${RESET}"
        echo "Install manually for your distro:"
        echo "  Ubuntu 22.04+:  sudo apt install python3-gi gir1.2-webkit2-4.1"
        echo "  Ubuntu 20.04:   sudo apt install python3-gi gir1.2-webkit2-4.0"
        exit 1
    fi
else
    echo -e "${GREEN}✔ WebKitGTK found${RESET}"
fi

# ── 4. create ~/.local/bin if needed ──────────
echo -e "${YELLOW}Checking ~/.local/bin...${RESET}"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
    echo -e "${GREEN}✔ Created:${RESET} $INSTALL_DIR"
else
    echo -e "${GREEN}✔ Exists:${RESET} $INSTALL_DIR"
fi

# ── 5. copy flutterff.py ──────────────────────
echo -e "${YELLOW}Installing flutterff...${RESET}"
cp "$SCRIPT_DIR/flutterff.py" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"
echo -e "${GREEN}✔ Installed to:${RESET} $INSTALL_PATH"

# ── 6. check PATH ─────────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}~/.local/bin is not in your PATH.${RESET}"
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo -e "  ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
    echo ""
    echo "Then run:  source ~/.bashrc"
else
    echo -e "${GREEN}✔ ~/.local/bin is already in PATH${RESET}"
fi

# ── 7. pre-warm uv cache (optional) ───────────
echo -e "${YELLOW}Pre-warming pywebview with uv...${RESET}"
uv run --script "$INSTALL_PATH" --version 2>/dev/null \
    && echo -e "${GREEN}✔ pywebview ready${RESET}" \
    || echo -e "${YELLOW}⚠ Could not pre-warm — will download on first run${RESET}"

echo ""
echo -e "${BOLD}${GREEN}✔ Setup complete!${RESET}"
echo ""
echo -e "Run inside any Flutter project:  ${CYAN}flutterff${RESET}"
echo -e "See all options:                 ${CYAN}flutterff --help${RESET}"
echo ""