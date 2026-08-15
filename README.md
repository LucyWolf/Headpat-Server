**Language / Sprache:** [🇬🇧 English](#headpat-server) | [🇩🇪 Deutsch](#headpat-server-1)

---

# Headpat Server

Windows/Linux app that bridges VRChat OSC contact data to the Headpat haptic device via Bluetooth.

## How it works

```
VRChat  →  OSC  →  Headpat Server  →  BLE  →  Headpat
```

- Receives OSC messages from VRChat on port 9001
- Detects `Headpat_Left` / `Headpat_Right` / `PatStrap_*` avatar parameters
- Scales contact depth (0.0–1.0) to motor intensity
- Sends motor commands directly via Bluetooth (BLE) — no Dongle required

## Features

- Direct BLE connection to the Headpat device (regular Bluetooth stick, no Dongle needed)
- Auto-reconnect to last known device on startup
- Save multiple Headpat devices with custom nicknames
- Intensity slider (saved between sessions)
- Sleep button to put the Headpat device to sleep
- Log console for status and debug output
- Automatic update detection (Headpat firmware + Server)

## Installation

### Windows
Download `HeadpatServer-Setup.exe` from [Releases](../../releases) and run it. Installs to `C:\Program Files\Headpat Server`.

### Linux
One-liner (downloads the latest release and installs it):

```bash
curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash
```

Or manually: download `headpat-server-linux.tar.gz` from [Releases](../../releases), extract it and run the installer.

```bash
mkdir headpat-server-linux && tar -xzf headpat-server-linux.tar.gz -C headpat-server-linux
cd headpat-server-linux
./install.sh
```

Either way, it sets up its own venv under `~/.local/share/headpat-server`, installs Python dependencies, and adds a menu entry. Uses `apt`/`dnf`/`pacman`/`zypper` (whichever is found) for system packages (tkinter, venv) if they're missing — may ask for your sudo password once. Run `./uninstall.sh` from an extracted copy to remove it again.

## Running from source

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python heatpett_server.py
```

## VRChat setup

Enable OSC in VRChat: **Settings → OSC → Enable**

Add contact receivers to your avatar with parameter names containing `headpat` or `patstrap`:
- `Headpat_Left` — left motor
- `Headpat_Right` — right motor
- `Headpat` — both motors

## Bluetooth pairing

1. Put the Headpat device into pairing mode (hold button 3s then release)
2. Open the server and click **+** in the connection area
3. The server scans for nearby Headpat devices — select yours and set a nickname
4. The address is saved — next launch reconnects automatically

## Firmware updates

The server checks GitHub for new firmware versions on startup. When an update is available, a **↑** badge appears in the title bar. Click it to open the update dialog.

To flash Headpat firmware: connect it via USB, double-tap the reset button, and copy `headpat-firmware.uf2` onto the drive that appears.

## Related

- [Headpat](https://github.com/LucyWolf/HeatPett) — Headpat device firmware

---

# Headpat Server

Windows/Linux-App, die VRChat-OSC-Kontaktdaten per Bluetooth an das Headpat-Gerät weiterleitet.

## So funktioniert es

```
VRChat  →  OSC  →  Headpat Server  →  BLE  →  Headpat
```

- Empfängt OSC-Nachrichten von VRChat auf Port 9001
- Erkennt `Headpat_Left` / `Headpat_Right` / `PatStrap_*` Avatar-Parameter
- Skaliert Kontakttiefe (0,0–1,0) auf Motor-Intensität
- Sendet Motorbefehle direkt per Bluetooth (BLE) — kein Dongle nötig

## Funktionen

- Direkte BLE-Verbindung zum Headpat-Gerät (normaler Bluetooth-Stick, kein Dongle nötig)
- Automatische Wiederverbindung beim Start
- Mehrere Headpat-Geräte mit eigenen Spitznamen speichern
- Intensitätsregler (wird zwischen Sitzungen gespeichert)
- Sleep-Button zum Schlafen des Headpat-Geräts
- Log-Konsole für Status und Debugging
- Automatische Update-Erkennung (Headpat-Firmware + Server)

## Installation

### Windows
`HeadpatServer-Setup.exe` von [Releases](../../releases) herunterladen und ausführen. Installiert sich nach `C:\Program Files\Headpat Server`.

### Linux
Einzeiler (lädt das neueste Release und installiert es):

```bash
curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash
```

Oder manuell: `headpat-server-linux.tar.gz` von [Releases](../../releases) herunterladen, entpacken und den Installer ausführen.

```bash
mkdir headpat-server-linux && tar -xzf headpat-server-linux.tar.gz -C headpat-server-linux
cd headpat-server-linux
./install.sh
```

So oder so wird ein eigenes venv unter `~/.local/share/headpat-server` angelegt, die Python-Abhängigkeiten installiert und ein Menüeintrag eingerichtet. Nutzt `apt`/`dnf`/`pacman`/`zypper` (je nachdem was gefunden wird) für System-Pakete (tkinter, venv), falls sie fehlen — fragt dann evtl. einmalig nach dem sudo-Passwort. Mit `./uninstall.sh` aus einer entpackten Kopie lässt es sich wieder entfernen.

## Aus dem Quellcode starten

Benötigt Python 3.11+.

```bash
pip install -r requirements.txt
python heatpett_server.py
```

## VRChat-Einrichtung

OSC in VRChat aktivieren: **Einstellungen → OSC → Aktivieren**

Kontakt-Receiver im Avatar mit Parameternamen, die `headpat` oder `patstrap` enthalten:
- `Headpat_Left` — linker Motor
- `Headpat_Right` — rechter Motor
- `Headpat` — beide Motoren

## Bluetooth-Kopplung

1. Headpat in den Pairing-Modus versetzen (Knopf 3s halten, dann loslassen)
2. Server öffnen und auf **+** im Verbindungsbereich klicken
3. Der Server sucht nach Headpat-Geräten — gewünschtes auswählen und Spitzname vergeben
4. Die Adresse wird gespeichert — beim nächsten Start verbindet er sich automatisch

## Firmware-Updates

Der Server prüft beim Start GitHub auf neue Firmware-Versionen. Wenn ein Update verfügbar ist, erscheint ein **↑**-Badge in der Titelleiste. Klick darauf öffnet den Update-Dialog.

Headpat-Firmware flashen: Per USB verbinden, Reset-Button doppelt drücken und `headpat-firmware.uf2` auf das erscheinende Laufwerk kopieren.

## Verwandte Projekte

- [Headpat](https://github.com/LucyWolf/HeatPett) — Headpat-Geräte-Firmware
