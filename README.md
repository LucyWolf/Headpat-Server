# Headpat Server

Windows app that bridges VRChat OSC contact data to the Headpat haptic headpat device.

## How it works

```
VRChat  →  OSC  →  Headpat Server  →  USB Serial  →  Dongle  →  BLE  →  Headpat
```

- Receives OSC messages from VRChat on port 9001
- Detects `Headpat_Left` / `Headpat_Right` / `PatStrap_*` avatar parameters
- Scales contact depth (0.0–1.0) to motor intensity
- Sends motor commands via USB serial to the Headpat Dongle

## Features

- Auto-connect to dongle on startup
- Intensity slider (saved between sessions)
- OSC debug console with verbose toggle
- Config saved to `%APPDATA%\HeadpatServer\config.json`

## Installation

Download `HeadpatServer-Setup-v2.3.exe` from [Releases](../../releases) and run it. No admin rights required.

## Running from source

Requires Python 3.11+.

```bash
pip install pyserial python-osc
python heatpett_server.py
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv run --with pyserial --with python-osc heatpett_server.py
```

## VRChat setup

Enable OSC in VRChat: **Settings → OSC → Enable**

Add contact receivers to your avatar with parameter names containing `headpat` or `patstrap`:
- `Headpat_Left` — left motor
- `Headpat_Right` — right motor
- `Headpat` — both motors

## Related

- [Headpat](https://github.com/LucyWolf/Headpat) — Headpat device firmware
- [dongel_NRF](https://github.com/LucyWolf/dongel_NRF) — Dongle firmware
