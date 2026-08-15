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
Download `headpat-server-setup.exe` from [Releases](../../releases) and run it. Installs to `C:\Program Files\Headpat Server`.

### Linux
There's no single "double-click .exe" equivalent on Linux (every distro has its own package format) — pick the double-click installer for your distro family from [Releases](../../releases/latest):

| Distro | Download |
|---|---|
| Debian / Ubuntu (and derivatives) | [`headpat-server-deb-installer.desktop`](../../releases/latest/download/headpat-server-deb-installer.desktop) |
| Arch / CachyOS / Manjaro | [`headpat-server-arch-installer.desktop`](../../releases/latest/download/headpat-server-arch-installer.desktop) |
| Anything else (Fedora, openSUSE, …) | [`headpat-server-installer.desktop`](../../releases/latest/download/headpat-server-installer.desktop) |

Download, then double-click it in your file manager. The first time you run a downloaded `.desktop` file, most file managers (e.g. GNOME Files, Dolphin) ask you to confirm trust once ("Allow Launching") — same idea as a Windows SmartScreen prompt for an unsigned `.exe`. The Debian/Arch ones install system-wide (to `/opt/headpat-server`, one privilege-elevation prompt, like Windows UAC) via `apt`/`pacman`; the generic one installs per-user, no elevation needed.

<details>
<summary>Prefer the terminal?</summary>

```bash
# Debian/Ubuntu
sudo apt install ./headpat-server-all.deb

# Arch/CachyOS/Manjaro
sudo pacman -U headpat-server-any.pkg.tar.zst

# Any other distro (one-liner, installs to ~/.local, no root needed)
curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash
```

All `.deb`/`.pkg.tar.zst`/`headpat-server-linux.tar.gz` files are also on the [Releases](../../releases/latest) page if you'd rather grab them manually. `python-osc`/`bleak` (not packaged for any distro) get installed into a small per-user venv (`~/.local/share/headpat-server/venv`) automatically on first launch. `./uninstall.sh` (from the extracted tarball) removes a per-user install again; `sudo apt remove`/`sudo pacman -R headpat-server` removes a system one.
</details>

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
`headpat-server-setup.exe` von [Releases](../../releases) herunterladen und ausführen. Installiert sich nach `C:\Program Files\Headpat Server`.

### Linux
Es gibt kein einzelnes ".exe-Doppelklick"-Äquivalent auf Linux (jede Distro hat ihr eigenes Paketformat) — nimm den Doppelklick-Installer für deine Distro-Familie von [Releases](../../releases/latest):

| Distro | Download |
|---|---|
| Debian / Ubuntu (und Derivate) | [`headpat-server-deb-installer.desktop`](../../releases/latest/download/headpat-server-deb-installer.desktop) |
| Arch / CachyOS / Manjaro | [`headpat-server-arch-installer.desktop`](../../releases/latest/download/headpat-server-arch-installer.desktop) |
| Alles andere (Fedora, openSUSE, …) | [`headpat-server-installer.desktop`](../../releases/latest/download/headpat-server-installer.desktop) |

Herunterladen, dann im Dateimanager doppelklicken. Beim ersten Start einer heruntergeladenen `.desktop`-Datei fragen die meisten Dateimanager (z.B. GNOME Files, Dolphin) einmalig nach Vertrauen ("Ausführen erlauben") — ähnlich wie Windows SmartScreen bei einer unsignierten `.exe`. Die Debian/Arch-Installer installieren system-weit (nach `/opt/headpat-server`, ein Rechte-Erhöhungs-Dialog, wie Windows UAC) über `apt`/`pacman`; der generische installiert pro Nutzer, ohne Rechte-Erhöhung.

<details>
<summary>Lieber per Terminal?</summary>

```bash
# Debian/Ubuntu
sudo apt install ./headpat-server-all.deb

# Arch/CachyOS/Manjaro
sudo pacman -U headpat-server-any.pkg.tar.zst

# Alle anderen Distros (Einzeiler, installiert nach ~/.local, kein root nötig)
curl -fsSL https://raw.githubusercontent.com/LucyWolf/Headpat-Server/main/bootstrap.sh | bash
```

Alle `.deb`-/`.pkg.tar.zst`-/`headpat-server-linux.tar.gz`-Dateien liegen auch auf der [Releases](../../releases/latest)-Seite, falls du sie lieber manuell holst. `python-osc`/`bleak` (für keine Distro paketiert) landen beim ersten Start automatisch in einem kleinen venv pro Nutzer (`~/.local/share/headpat-server/venv`). `./uninstall.sh` (aus dem entpackten Tarball) entfernt eine Pro-Nutzer-Installation wieder; `sudo apt remove`/`sudo pacman -R headpat-server` entfernt eine System-Installation.
</details>

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
