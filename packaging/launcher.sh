#!/usr/bin/env bash
# Headpat Server — Launcher fuer system-weit installierte Pakete (.deb/Arch).
# Die App selbst liegt unter /opt/headpat-server (root-Eigentum, von dpkg/
# pacman verwaltet). Tkinter/venv-Modul kommen als echte Paketabhaengigkeiten
# vom Paketmanager mit. python-osc und bleak gibt es nicht als Debian/Arch-
# Pakete -- die landen bei erstem Start in einem eigenen, pro Nutzer venv
# unter ~/.local/share/headpat-server/venv (kein root noetig dafuer).
set -euo pipefail

APP=/opt/headpat-server/heatpett_server.py
VENV="$HOME/.local/share/headpat-server/venv"

setup() {
    echo "10"; echo "# Erstinstallation: richte Python-Umgebung ein…"
    mkdir -p "$(dirname "$VENV")"
    python3 -m venv "$VENV"
    echo "40"; echo "# Installiere Abhaengigkeiten…"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet pyserial python-osc pillow certifi bleak
    echo "100"; echo "# Fertig"
}

if [ ! -x "$VENV/bin/python" ]; then
    if command -v zenity >/dev/null 2>&1 && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        setup | zenity --progress --title="Headpat Server" \
            --text="Erstinstallation wird abgeschlossen…" \
            --auto-close --no-cancel --width=380
    else
        echo "== Headpat Server: Erstinstallation =="
        mkdir -p "$(dirname "$VENV")"
        python3 -m venv "$VENV"
        "$VENV/bin/pip" install --quiet --upgrade pip
        "$VENV/bin/pip" install --quiet pyserial python-osc pillow certifi bleak
    fi
fi

exec "$VENV/bin/python" "$APP" "$@"
