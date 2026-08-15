#!/usr/bin/env bash
# Headpat Server — One-Line-Installer
# Laedt das neueste Linux-Release von GitHub, entpackt es in ein Temp-
# Verzeichnis und ruft von dort das eigentliche install.sh auf.
#
#   curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash
#
set -euo pipefail

REPO="LucyWolf/Headpat-Server"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Headpat Server — Installer wird geladen =="

URL=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | python3 -c '
import json, sys
d = json.load(sys.stdin)
for a in d.get("assets", []):
    if a["name"] == "headpat-server-linux.tar.gz":
        print(a["browser_download_url"])
        break
')

if [ -z "$URL" ]; then
    echo "FEHLER: Konnte die Download-URL fuer das neueste Release nicht ermitteln." >&2
    echo "Manuell probieren: https://github.com/$REPO/releases/latest" >&2
    exit 1
fi

echo "Lade $URL…"
curl -fsSL "$URL" -o "$TMP/headpat-server-linux.tar.gz"
tar -xzf "$TMP/headpat-server-linux.tar.gz" -C "$TMP"
chmod +x "$TMP/install.sh"
exec "$TMP/install.sh"
