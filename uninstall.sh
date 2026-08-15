#!/usr/bin/env bash
# Headpat Server — Linux Uninstaller
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/headpat-server"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/headpat-server"
rm -f "$DESKTOP_DIR/headpat-server.desktop"
rm -f "$ICON_DIR/headpat-server.png"

echo "Headpat Server wurde entfernt. Gespeicherte Einstellungen unter ~/.config/HeadpatServer bleiben erhalten."
