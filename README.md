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
There's no single "double-click .exe" equivalent on Linux (every distro has its own package format), so there's a real, native package for the two most common families, plus a generic fallback for everything else.

**Debian / Ubuntu (and derivatives)**: download the `.deb` from [Releases](../../releases/latest) and install it — double-click it (opens your software center / GDebi) or:
```bash
sudo apt install ./headpat-server_*.deb
```

**Arch / CachyOS / Manjaro**: download the `.pkg.tar.zst` from [Releases](../../releases/latest) and install it:
```bash
sudo pacman -U headpat-server-*.pkg.tar.zst
```

Both install system-wide (to `/opt/headpat-server`, with a menu entry and a launcher at `/usr/bin/headpat-server`) and declare `tkinter`/`venv` as real package dependencies, resolved automatically by `apt`/`pacman` during install — that's the one privilege-elevation prompt, same idea as Windows UAC for the `.exe` installer. `python-osc` and `bleak` aren't packaged for any distro, so those get installed into a small per-user venv (`~/.local/share/headpat-server/venv`) automatically on first launch, with a graphical progress dialog if `zenity` is installed. Update by installing the newer package the same way — the app won't try to self-update if it detects it was installed this way.

**Other distros / no native package**: covers Fedora, openSUSE, and anything else with `apt`/`dnf`/`pacman`/`zypper` available. Same idea (venv under `~/.local/share/headpat-server`, self-updates from inside the app), just per-user instead of system-wide.

- Double-click installer (closest to a Windows-style setup wizard): download [`headpat-server-installer.desktop`](../../releases/latest/download/headpat-server-installer.desktop), then double-click it in your file manager. The first time you run a downloaded `.desktop` file, most file managers (e.g. GNOME Files) ask you to confirm trust once ("Allow Launching") — same idea as a Windows SmartScreen prompt for an unsigned `.exe`.
- One-liner (terminal): `curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash`
- Manual: download `headpat-server-linux.tar.gz` from [Releases](../../releases), extract it and run `./install.sh` (or right-click → "Run"/"Execute" for the graphical mode). `./uninstall.sh` from the same extracted copy removes it again.

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
Es gibt kein einzelnes ".exe-Doppelklick"-Äquivalent auf Linux (jede Distro hat ihr eigenes Paketformat) — deshalb gibt's für die zwei größten Familien ein echtes natives Paket, plus einen generischen Fallback für den Rest.

**Debian / Ubuntu (und Derivate)**: `.deb` von [Releases](../../releases/latest) herunterladen und installieren — doppelklicken (öffnet Software-Center/GDebi) oder:
```bash
sudo apt install ./headpat-server_*.deb
```

**Arch / CachyOS / Manjaro**: `.pkg.tar.zst` von [Releases](../../releases/latest) herunterladen und installieren:
```bash
sudo pacman -U headpat-server-*.pkg.tar.zst
```

Beide installieren system-weit (nach `/opt/headpat-server`, mit Menüeintrag und Launcher unter `/usr/bin/headpat-server`) und deklarieren `tkinter`/`venv` als echte Paketabhängigkeiten, die `apt`/`pacman` beim Installieren automatisch auflösen — das ist der eine Rechte-Erhöhungs-Dialog, ähnlich wie Windows UAC beim `.exe`-Installer. `python-osc` und `bleak` gibt's für keine Distro als Paket, die landen beim ersten Start automatisch in einem kleinen venv pro Nutzer (`~/.local/share/headpat-server/venv`), mit grafischer Fortschrittsanzeige falls `zenity` installiert ist. Update per Neuinstallation des neueren Pakets — die App versucht sich nicht selbst zu aktualisieren, wenn sie erkennt, dass sie so installiert wurde.

**Andere Distros / kein natives Paket**: deckt Fedora, openSUSE und alles mit `apt`/`dnf`/`pacman`/`zypper` ab. Gleiches Prinzip (venv unter `~/.local/share/headpat-server`, Selbst-Update aus der App), nur pro Nutzer statt system-weit.

- Doppelklick-Installer (kommt einem Windows-Setup-Assistenten am nächsten): [`headpat-server-installer.desktop`](../../releases/latest/download/headpat-server-installer.desktop) herunterladen, dann im Dateimanager doppelklicken. Beim ersten Start einer heruntergeladenen `.desktop`-Datei fragen die meisten Dateimanager (z.B. GNOME Files) einmalig nach Vertrauen ("Ausführen erlauben") — ähnlich wie Windows SmartScreen bei einer unsignierten `.exe`.
- Einzeiler (Terminal): `curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash`
- Manuell: `headpat-server-linux.tar.gz` von [Releases](../../releases) herunterladen, entpacken und `./install.sh` ausführen (oder Rechtsklick → "Ausführen" für den grafischen Modus). `./uninstall.sh` aus derselben entpackten Kopie entfernt es wieder.

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
