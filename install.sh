#!/usr/bin/env bash
# Headpat Server — Linux Installer
# Legt ein eigenes venv an, installiert Python-Abhaengigkeiten und richtet
# einen Menue-Eintrag ein. Kann auch fuer Updates erneut ausgefuehrt werden
# (dann meist ohne sudo, da System-Pakete schon vorhanden sind).
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/headpat-server"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Headpat Server Installer =="

# ── System-Abhaengigkeiten ────────────────────────────────────────────────
# Nur anfassen wenn wirklich was fehlt, damit ein Update-Lauf (aus der
# laufenden App heraus gestartet) i.d.R. ohne sudo-Passwortabfrage durchlaeuft.
if ! python3 -c "import tkinter" >/dev/null 2>&1 || ! python3 -c "import venv" >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installiere fehlende System-Pakete (python3-venv, python3-tk)…"
        sudo apt-get update -qq
        sudo apt-get install -y python3-venv python3-tk
    else
        echo "FEHLER: tkinter und/oder venv fehlen, apt-get ist nicht verfuegbar." >&2
        echo "Bitte python3-venv und python3-tk manuell ueber deinen Paketmanager installieren." >&2
        exit 1
    fi
fi

# ── venv + Python-Abhaengigkeiten ─────────────────────────────────────────
mkdir -p "$INSTALL_DIR"
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet pyserial python-osc pillow certifi bleak

# ── App-Dateien ────────────────────────────────────────────────────────────
cp "$SCRIPT_DIR/heatpett_server.py" "$INSTALL_DIR/heatpett_server.py"
cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/icon.png"

# ── Launcher ───────────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/headpat-server" << LAUNCHER
#!/usr/bin/env bash
exec "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/heatpett_server.py" "\$@"
LAUNCHER
chmod +x "$BIN_DIR/headpat-server"

# ── Menue-Eintrag ────────────────────────────────────────────────────────
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
cp "$SCRIPT_DIR/icon.png" "$ICON_DIR/headpat-server.png"
cat > "$DESKTOP_DIR/headpat-server.desktop" << DESKTOP
[Desktop Entry]
Name=Headpat Server
Exec=$BIN_DIR/headpat-server
Icon=headpat-server
Type=Application
Categories=Utility;
DESKTOP

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    echo "Hinweis: $BIN_DIR ist nicht in deinem PATH — Start ueber das Anwendungsmenue geht trotzdem."
fi

echo "Fertig! Start ueber das Anwendungsmenue oder: $BIN_DIR/headpat-server"
