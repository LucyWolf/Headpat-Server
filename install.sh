#!/usr/bin/env bash
# Headpat Server — Linux Installer
# Legt ein eigenes venv an, installiert Python-Abhaengigkeiten und richtet
# einen Menue-Eintrag ein. Kann auch fuer Updates erneut ausgefuehrt werden
# (dann meist ohne Passwortabfrage, da System-Pakete schon vorhanden sind).
#
# Zeigt eine grafische Fortschrittsanzeige (zenity) statt Terminal-Text,
# wenn verfuegbar -- z.B. bei Doppelklick/"Ausfuehren" im Dateimanager statt
# Aufruf aus einem Terminal. Faellt sonst automatisch auf Terminal-Text zurueck.
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/headpat-server"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GUI=0
if command -v zenity >/dev/null 2>&1 && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    GUI=1
fi

msg() { if [ "$GUI" = "1" ]; then echo "# $1"; else echo "== $1 =="; fi; }
pct() { [ "$GUI" = "1" ] && echo "$1"; true; }

# Installiert System-Pakete per grafischem Passwort-Dialog (pkexec, oder
# zenity --password als Fallback) statt Terminal-sudo, wenn im GUI-Modus.
as_root() {
    if [ "$GUI" = "1" ]; then
        if command -v pkexec >/dev/null 2>&1; then
            pkexec "$@"
            return
        fi
        local pw
        pw=$(zenity --password --title="Headpat Server") || exit 1
        echo "$pw" | sudo -S "$@"
        return
    fi
    sudo "$@"
}

do_install() {
    pct 0
    msg "Pruefe System-Abhaengigkeiten…"
    if ! python3 -c "import tkinter" >/dev/null 2>&1 || ! python3 -c "import venv" >/dev/null 2>&1; then
        if command -v apt-get >/dev/null 2>&1; then
            as_root apt-get update -qq
            as_root apt-get install -y -qq python3-venv python3-tk
        elif command -v dnf >/dev/null 2>&1; then
            as_root dnf install -y -q python3-tkinter
        elif command -v pacman >/dev/null 2>&1; then
            as_root pacman -S --needed --noconfirm tk
        elif command -v zypper >/dev/null 2>&1; then
            as_root zypper install -y python3-tk
        else
            echo "FEHLER: tkinter und/oder venv fehlen, kein unterstuetzter Paketmanager" >&2
            echo "(apt/dnf/pacman/zypper) gefunden. Bitte manuell ein Paket installieren," >&2
            echo "das tkinter fuer Python 3 bereitstellt (venv ist meist schon dabei)." >&2
            exit 1
        fi
    fi
    pct 20

    msg "Richte Python-Umgebung ein…"
    mkdir -p "$INSTALL_DIR"
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        python3 -m venv "$INSTALL_DIR/venv"
    fi
    pct 35

    msg "Installiere Python-Abhaengigkeiten…"
    "$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
    "$INSTALL_DIR/venv/bin/pip" install --quiet pyserial python-osc pillow certifi bleak
    pct 75

    msg "Kopiere Programmdateien…"
    cp "$SCRIPT_DIR/heatpett_server.py" "$INSTALL_DIR/heatpett_server.py"
    cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/icon.png"
    pct 85

    msg "Richte Menueeintrag ein…"
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/headpat-server" << LAUNCHER
#!/usr/bin/env bash
exec "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/heatpett_server.py" "\$@"
LAUNCHER
    chmod +x "$BIN_DIR/headpat-server"

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
    pct 100
    msg "Fertig!"
}

if [ "$GUI" = "1" ]; then
    set +e
    do_install | zenity --progress --title="Headpat Server" \
        --text="Installation wird vorbereitet…" --percentage=0 \
        --auto-close --no-cancel --width=380
    rc=${PIPESTATUS[0]}
    set -e
    if [ "$rc" -ne 0 ]; then
        zenity --error --title="Headpat Server" \
            --text="Installation fehlgeschlagen (Code $rc).\nFuer Details im Terminal ausfuehren: bash install.sh" \
            --width=320
        exit "$rc"
    fi
    zenity --info --title="Headpat Server" \
        --text="Installation abgeschlossen!\n\nStart ueber das Anwendungsmenue oder:\n$BIN_DIR/headpat-server" \
        --width=320
else
    do_install
    if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
        echo "Hinweis: $BIN_DIR ist nicht in deinem PATH — Start ueber das Anwendungsmenue geht trotzdem."
    fi
    echo "Fertig! Start ueber das Anwendungsmenue oder: $BIN_DIR/headpat-server"
fi
