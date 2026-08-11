[🇬🇧 English](README.md) | 🇩🇪 Deutsch

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
`HeadpatServer-x86_64.AppImage` von [Releases](../../releases) herunterladen, ausführbar machen und starten.

```bash
chmod +x HeadpatServer-x86_64.AppImage
./HeadpatServer-x86_64.AppImage
```

## Aus dem Quellcode starten

Benötigt Python 3.11+.

```bash
pip install python-osc pillow bleak
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
