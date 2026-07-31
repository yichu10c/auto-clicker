#!/bin/bash
# Build Auto Clicker into a standalone executable
# Run: chmod +x build.sh && ./build.sh

set -e

echo "Installing dependencies..."
pip install pynput pyinstaller

echo "Building executable (this may take ~30 seconds)..."
pyinstaller \
  --onefile \
  --name "AutoClicker" \
  --add-data "$(python -c 'import pynput; print(pynput.__path__[0])'):pynput" \
  --noconfirm \
  auto_clicker.py

echo ""
echo "✅ Done! Executable is at: dist/AutoClicker"
echo ""
echo "macOS/Linux note: If you see 'blocked by system' on first run, run:"
echo "  xattr -d com.apple.quarantine dist/AutoClicker   (macOS)"
echo "  chmod +x dist/AutoClicker                        (Linux)"
