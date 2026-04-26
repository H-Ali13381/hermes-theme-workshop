#!/usr/bin/env bash
# =============================================================================
# linux-ricing setup script
# Installs dependencies, creates dirs, makes ricer.py executable,
# and symlinks 'ricer' into ~/.local/bin for convenience.
# Run once after cloning or updating the skill.
# =============================================================================
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RICER_PY="$SKILL_DIR/scripts/ricer.py"
CACHE_DIR="$HOME/.cache/linux-ricing"
LOCAL_BIN="$HOME/.local/bin"
SYMLINK="$LOCAL_BIN/ricer"

echo "=== linux-ricing setup ==="
echo "Skill dir : $SKILL_DIR"
echo ""

# --- 1. Python deps ---
echo "[1/4] Installing Python dependencies..."
if python3 -c "import jinja2" 2>/dev/null; then
    echo "  jinja2  : already installed"
else
    pip3 install --quiet jinja2 && echo "  jinja2  : installed" || echo "  jinja2  : FAILED (non-fatal, fallback renderer available)"
fi

if python3 -c "import PIL" 2>/dev/null; then
    echo "  pillow  : already installed"
else
    pip3 install --quiet pillow && echo "  pillow  : installed" || echo "  pillow  : FAILED (non-fatal, image theming will be skipped)"
fi

# --- 2. Make ricer.py executable ---
echo ""
echo "[2/4] Setting permissions..."
chmod +x "$RICER_PY"
echo "  ricer.py : chmod +x done"

# --- 3. Create cache dirs ---
echo ""
echo "[3/4] Creating cache directories..."
mkdir -p "$CACHE_DIR/backups"
mkdir -p "$CACHE_DIR/current/history"
echo "  $CACHE_DIR : created"

# --- 4. Symlink into ~/.local/bin ---
echo ""
echo "[4/4] Symlinking ricer -> ~/.local/bin/ricer..."
mkdir -p "$LOCAL_BIN"
if [ -L "$SYMLINK" ]; then
    rm "$SYMLINK"
fi
ln -s "$RICER_PY" "$SYMLINK"
echo "  symlink  : $SYMLINK -> $RICER_PY"

# Check PATH
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo ""
    echo "  WARNING: $LOCAL_BIN is not in your PATH."
    echo "  Add this to ~/.bashrc or ~/.zshrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# --- Smoke test ---
echo ""
echo "=== Smoke test ==="
if ricer status 2>/dev/null; then
    echo ""
    echo "Setup complete. Run 'ricer --help' to get started."
else
    echo ""
    echo "Symlink not yet in PATH — run directly:"
    echo "  python3 $RICER_PY status"
fi
