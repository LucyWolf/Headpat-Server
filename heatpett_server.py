#!/usr/bin/env python3
"""Headpat Server v2.6 — VRChat OSC <-> Headpat Dongle USB bridge"""

import tkinter as tk
from tkinter import ttk, filedialog as tk_filedialog
import threading
import queue
import collections
import json
import re
import time
import os
import sys
import urllib.request
import urllib.error
import tempfile
import shutil

try:
    import serial
    import serial.tools.list_ports
    SERIAL_OK = True
except Exception:
    SERIAL_OK = False

try:
    from pythonosc import dispatcher, osc_server
    OSC_OK = True
except Exception:
    OSC_OK = False

try:
    from PIL import Image, ImageTk, ImageDraw as _PilDraw
    PIL_OK = True
except Exception:
    PIL_OK = False

# ── Crash logger ──────────────────────────────────────────────────────────────
def _setup_crash_log():
    try:
        import traceback as _tb
        _log_dir  = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HeadpatServer")
        os.makedirs(_log_dir, exist_ok=True)
        _log_path = os.path.join(_log_dir, "crash.log")

        def _write(header, exc_type, exc_val, exc_tb):
            try:
                with open(_log_path, "a", encoding="utf-8") as _f:
                    _f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {header} ===\n")
                    _tb.print_exception(exc_type, exc_val, exc_tb, file=_f)
            except Exception:
                pass

        def _excepthook(et, ev, etb):
            _write("(main thread)", et, ev, etb)
            sys.__excepthook__(et, ev, etb)

        def _thread_hook(args):
            _write("(thread)", args.exc_type, args.exc_value, args.exc_traceback)

        sys.excepthook = _excepthook
        threading.excepthook = _thread_hook
    except Exception:
        pass

_setup_crash_log()

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = "#0d0f14"
BG_TITLE = "#11141c"
BG_BTN   = "#181b24"
BG_BTN_A = "#1e2236"
BORDER   = "#252b3a"
FG       = "#e8ecf8"
FG_DIM   = "#7a8299"
ACCENT   = "#4080f5"
GREEN    = "#3dd68c"
RED      = "#f06b6b"
YELLOW   = "#fbbf24"
OSC_COL  = "#1a2d60"
SEG_CONT = "#080a10"

# ── Config ────────────────────────────────────────────────────────────────────
BAUD          = 115200
OSC_RX_PORT   = 9001
OSC_HOST      = "127.0.0.1"
VRC_TIMEOUT   = 5.0
INFO_INTERVAL = 5.0
BAT_INTERVAL  = 30.0
# Matches "headpat"/"patstrap" anywhere; "left"/"right" only as whole words
# so that e.g. "Upright", "GestureLeft" do NOT trigger the motor.
_MOTOR_RE = re.compile(r'headpat|patstrap|\bleft\b|\bright\b')

SERVER_VERSION  = "v3.7.2"
GITHUB_OWNER    = "LucyWolf"
HEADPAT_REPO    = "Headpat"

SERVER_REPO     = "Headpat-Server"
NRF52_LABELS    = {"NRF52BOOT", "NICENANO"}
UPDATE_INTERVAL = 300

_BASE     = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ICON_PATH = os.path.join(_BASE, "icon.png")

if os.name == "nt":
    CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HeadpatServer")
else:
    CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")), "HeadpatServer")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# ── Lang (loaded once at startup) ─────────────────────────────────────────────
_LANG = "de"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
        _cfg_boot = json.load(_f)
        _LANG = _cfg_boot.get("lang", "de")
except Exception:
    pass

# ── i18n ──────────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "de": {
        "settings_title": "Einstellungen",
        "sec_connection": "Verbindung",
        "sec_board": "Dongle-Board",
        "sec_commands": "Dongle-Befehle",
        "sec_versions": "Versionen",
        "sec_language": "Sprache",
        "btn_search": "Suchen",
        "btn_check_updates": "Jetzt auf Updates prüfen",
        "btn_refresh": "Aktualisieren",
        "upd_available": "Verfügbare Updates",
        "upd_usb_hint": "Dongle & Headpat müssen per USB\nmit dem PC verbunden sein.",
        "upd_all_ok": "Alles aktuell.",
        "btn_close": "Schließen",
        "btn_update": "Update →",
        "btn_flash": "Flashen →",
        "hp_flash_title": "Headpat Update",
        "hp_flash_hint": "Headpat per USB anschließen,\ndann Port auswählen und Flashen drücken.",
        "btn_cancel": "Abbrechen",
        "downloading": "UF2 wird heruntergeladen…",
    },
    "en": {
        "settings_title": "Settings",
        "sec_connection": "Connection",
        "sec_board": "Dongle Board",
        "sec_commands": "Dongle Commands",
        "sec_versions": "Versions",
        "sec_language": "Language",
        "btn_search": "Search",
        "btn_check_updates": "Check for Updates Now",
        "btn_refresh": "Refresh",
        "upd_available": "Available Updates",
        "upd_usb_hint": "Dongle & Headpat must be connected\nvia USB for firmware updates.",
        "upd_all_ok": "Everything up to date.",
        "btn_close": "Close",
        "btn_update": "Update →",
        "btn_flash": "Flash →",
        "hp_flash_title": "Headpat Update",
        "hp_flash_hint": "Connect Headpat via USB,\nthen select the port and press Flash.",
        "btn_cancel": "Cancel",
        "downloading": "Downloading UF2…",
    },
}

def _t(key, **kwargs):
    text = TRANSLATIONS.get(_LANG, TRANSLATIONS["de"]).get(key, TRANSLATIONS["de"].get(key, key))
    return text.format(**kwargs) if kwargs else text


class RoundedBtn(tk.Canvas):
    """Rounded rectangle button — PIL-rendered for anti-aliased corners."""
    _SC = 3  # supersampling scale

    def __init__(self, parent, text, command, w=80, h=30, r=10,
                 fill=BG_BTN, fg=FG, hover=BG_BTN_A, press=None,
                 hover_fg=None, font_size=10, font_spec=None, border_col=None, p_bg=BG,
                 img_normal=None, img_hover=None, **kw):
        super().__init__(parent, width=w, height=h,
                         bg=p_bg, highlightthickness=0, cursor="hand2", **kw)
        self._text       = text
        self._cmd        = command
        self._bw, self._bh, self._br = w, h, r
        self._fill, self._fg, self._hover = fill, fg, hover
        self._press      = press or hover
        self._hover_fg   = hover_fg if hover_fg is not None else fg
        self._font_size  = font_size
        self._font_spec  = font_spec if font_spec is not None else ("Segoe UI", font_size)
        self._border_col = border_col
        self._p_bg       = p_bg
        self._photo      = None
        self._img_normal = img_normal
        self._img_hover  = img_hover
        self._icon_ref   = None
        self._draw(fill, fg)
        self.bind("<Enter>",          lambda _: self._draw(self._hover, self._hover_fg))
        self.bind("<Leave>",          lambda _: self._draw(self._fill,  self._fg))
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    @staticmethod
    def _hx(c):
        return int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)

    def _make_photo(self, fill_col, border_col=None):
        sc = self._SC
        W, H = self._bw * sc, self._bh * sc
        R = min(self._br * sc, W // 2, H // 2)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d   = _PilDraw.Draw(img)
        fc  = self._hx(fill_col) + (255,)
        if border_col:
            bc = self._hx(border_col) + (255,)
            d.rounded_rectangle([0, 0, W-1, H-1], radius=R, fill=fc, outline=bc, width=sc)
        else:
            d.rounded_rectangle([0, 0, W-1, H-1], radius=R, fill=fc)
        img  = img.resize((self._bw, self._bh), Image.LANCZOS)
        base = Image.new("RGBA", (self._bw, self._bh),
                         self._hx(self._p_bg) + (255,))
        base.alpha_composite(img)
        return ImageTk.PhotoImage(base.convert("RGB"))

    def _poly_fallback(self, color, border_col):
        r = min(self._br, self._bw//2, self._bh//2)
        w, h = self._bw, self._bh
        pts = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
        ol = border_col if border_col else color
        self.create_polygon(pts, smooth=True, splinesteps=64, fill=color, outline=ol)

    def _draw(self, color, text_fg=None):
        self.delete("all")
        w, h = self._bw, self._bh
        bc = self._border_col if (self._border_col and color == self._fill) else None
        if PIL_OK:
            try:
                photo = self._make_photo(color, bc)
                self._photo = photo
                self.create_image(0, 0, anchor="nw", image=photo)
            except Exception:
                self._poly_fallback(color, bc)
        else:
            self._poly_fallback(color, bc)
        if self._img_normal is not None:
            is_active = (color != self._fill)
            img = self._img_hover if (is_active and self._img_hover) else self._img_normal
            self._icon_ref = img
            self.create_image(w // 2, h // 2, image=img, anchor="center")
        else:
            self.create_text(w//2, h//2, text=self._text,
                             fill=text_fg if text_fg is not None else self._fg,
                             font=self._font_spec)

    def _on_press(self, _):
        self._draw(self._press, self._hover_fg)
        self._cmd()

    def _on_release(self, _):
        self._draw(self._fill, self._fg)

    def set_style(self, fill, fg, hover=None, hover_fg=None):
        self._fill, self._fg = fill, fg
        self._hover    = hover or fill
        self._press    = hover or fill
        self._hover_fg = hover_fg if hover_fg is not None else fg
        self._draw(fill, fg)
        self.bind("<Enter>", lambda _: self._draw(self._hover, self._hover_fg))
        self.bind("<Leave>", lambda _: self._draw(self._fill,  self._fg))


class SegmentedControl(tk.Canvas):
    """Pill-style segmented control with a dark container background."""
    _SEG_HOVER = "#1e2a48"
    _SEG_DIM   = "#8a92b0"
    _SEG_HDIM  = "#c0c6df"

    def __init__(self, parent, labels, command, active=0,
                 seg_w=90, h=32, r_cont=9, r_seg=7, pad=3, p_bg=BG, **kw):
        self._labels  = labels
        self._active  = active
        self._cmd     = command
        self._seg_w   = seg_w
        self._h       = h
        self._r_cont  = r_cont
        self._r_seg   = r_seg
        self._pad     = pad
        self._hover   = -1
        n             = len(labels)
        total_w       = pad + seg_w * n + pad * (n - 1) + pad
        total_h       = pad * 2 + h
        super().__init__(parent, width=total_w, height=total_h,
                         bg=p_bg, highlightthickness=0, cursor="hand2", **kw)
        self._tw = total_w
        self._th = total_h
        self._draw()
        self.bind("<ButtonPress-1>", self._on_click)
        self.bind("<Motion>",        self._on_motion)
        self.bind("<Leave>",         self._on_leave)

    def _seg_x(self, i):
        return self._pad + i * (self._seg_w + self._pad)

    @staticmethod
    def _hx(c):
        return int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)

    def _draw(self):
        self.delete("all")
        if PIL_OK:
            try:
                self._draw_pil()
                return
            except Exception:
                pass
        self._draw_poly()

    def _draw_pil(self):
        sc = 3
        W, H = self._tw * sc, self._th * sc
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d   = _PilDraw.Draw(img)
        # Container
        sc_col = self._hx(SEG_CONT) + (255,)
        d.rounded_rectangle([0, 0, W-1, H-1], radius=self._r_cont*sc, fill=sc_col)
        # Segments
        for i, label in enumerate(self._labels):
            x1 = self._seg_x(i) * sc
            y1 = self._pad * sc
            x2 = x1 + self._seg_w * sc
            y2 = y1 + self._h * sc
            is_active = i == self._active
            is_hover  = i == self._hover and not is_active
            if is_active:
                col = self._hx(ACCENT) + (255,)
                d.rounded_rectangle([x1, y1, x2, y2], radius=self._r_seg*sc, fill=col)
            elif is_hover:
                col = self._hx(self._SEG_HOVER) + (220,)
                d.rounded_rectangle([x1, y1, x2, y2], radius=self._r_seg*sc, fill=col)
        img  = img.resize((self._tw, self._th), Image.LANCZOS)
        base = Image.new("RGBA", (self._tw, self._th),
                         self._hx(self.cget("bg")) + (255,))
        base.alpha_composite(img)
        photo = ImageTk.PhotoImage(base.convert("RGB"))
        self._photo = photo
        self.create_image(0, 0, anchor="nw", image=photo)
        # Labels drawn by tkinter (ClearType)
        for i, label in enumerate(self._labels):
            is_active = i == self._active
            is_hover  = i == self._hover and not is_active
            fg_c = "white" if is_active else (self._SEG_HDIM if is_hover else self._SEG_DIM)
            bold = "bold" if is_active else "normal"
            cx = self._seg_x(i) + self._seg_w // 2
            cy = self._pad + self._h // 2
            self.create_text(cx, cy, text=label, fill=fg_c,
                             font=("Inter", 11, bold))

    def _draw_poly(self):
        w, h, r = self._tw, self._th, self._r_cont
        pts = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
        self.create_polygon(pts, smooth=True, splinesteps=64, fill=SEG_CONT, outline=SEG_CONT)
        for i, label in enumerate(self._labels):
            x1 = self._seg_x(i)
            y1 = self._pad
            x2 = x1 + self._seg_w
            y2 = y1 + self._h
            is_active = i == self._active
            is_hover  = i == self._hover and not is_active
            if is_active:
                bg_c, fg_c, bold = ACCENT, "white", "bold"
            elif is_hover:
                bg_c, fg_c, bold = self._SEG_HOVER, self._SEG_HDIM, "normal"
            else:
                bg_c = None; fg_c = self._SEG_DIM; bold = "normal"
            if bg_c:
                r2 = self._r_seg
                p2 = [x1+r2,y1, x2-r2,y1, x2,y1, x2,y1+r2,
                      x2,y2-r2, x2,y2, x2-r2,y2, x1+r2,y2,
                      x1,y2, x1,y2-r2, x1,y1+r2, x1,y1]
                self.create_polygon(p2, smooth=True, splinesteps=64, fill=bg_c, outline=bg_c)
            cx = x1 + self._seg_w // 2
            cy = y1 + self._h // 2
            self.create_text(cx, cy, text=label, fill=fg_c,
                             font=("Inter", 11, bold))

    def _hit(self, x):
        for i in range(len(self._labels)):
            x1 = self._seg_x(i)
            if x1 <= x <= x1 + self._seg_w:
                return i
        return -1

    def _on_click(self, e):
        seg = self._hit(e.x)
        if 0 <= seg != self._active:
            self._active = seg
            self._draw()
            self._cmd(seg)

    def _on_motion(self, e):
        seg = self._hit(e.x)
        if seg != self._hover:
            self._hover = seg
            self._draw()

    def _on_leave(self, _):
        if self._hover != -1:
            self._hover = -1
            self._draw()

    def set_active(self, i):
        self._active = i
        self._draw()


class FancySlider(tk.Canvas):
    """Custom slider: blue fill left of thumb, dark track right."""
    def __init__(self, parent, variable, from_=0, to=100, command=None,
                 track_h=4, thumb_r=8, p_bg=BG, **kw):
        bh = thumb_r * 2 + 8
        super().__init__(parent, height=bh,
                         bg=p_bg, highlightthickness=0, cursor="hand2", **kw)
        self._var  = variable
        self._from = from_
        self._to   = to
        self._cmd  = command
        self._th   = track_h
        self._tr   = thumb_r
        self._bw   = 1
        self._bh   = bh
        self.bind("<Configure>",       self._on_cfg)
        self.bind("<ButtonPress-1>",   self._on_down)
        self.bind("<B1-Motion>",       self._on_move)
        self.bind("<ButtonRelease-1>", self._on_up)
        self._var.trace_add("write", lambda *_: self._redraw())

    def _on_cfg(self, e):
        self._bw, self._bh = e.width, e.height
        self._redraw()

    def _val_to_x(self, val):
        r = self._tr
        return r + (val - self._from) / max(self._to - self._from, 1) * (self._bw - 2 * r)

    def _x_to_val(self, x):
        r = self._tr
        t = (x - r) / max(self._bw - 2 * r, 1)
        return self._from + max(0.0, min(1.0, t)) * (self._to - self._from)

    @staticmethod
    def _hx(c):
        return int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)

    def _redraw(self):
        if self._bw <= 2:
            return
        self.delete("all")
        val = self._var.get()
        cx  = int(self._val_to_x(val))
        cy  = self._bh // 2
        r   = self._tr
        if PIL_OK:
            try:
                self._redraw_pil(cx, cy, r)
                return
            except Exception:
                pass
        # Fallback: aliased drawing
        y1, y2 = cy - self._th//2, cy + self._th//2
        rr = (y2-y1)//2
        for x1, x2, col in [(r, self._bw-r, "#1a2548"), (r, cx, ACCENT)]:
            if x2-x1 > 0:
                self.create_oval(x1, y1, x1+2*rr, y2, fill=col, outline=col)
                self.create_oval(x2-2*rr, y1, x2, y2, fill=col, outline=col)
                self.create_rectangle(x1+rr, y1, x2-rr, y2, fill=col, outline=col)
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill="white", outline=ACCENT, width=2)

    def _redraw_pil(self, cx, cy, r):
        # ── Track at 3× ──────────────────────────────────────────────────────
        sc    = 3
        W, H  = self._bw * sc, self._bh * sc
        img   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d     = _PilDraw.Draw(img)
        th_s  = self._th * sc
        r_s   = r * sc
        cx_s  = cx * sc
        cy_s  = cy * sc
        y1_s  = cy_s - th_s // 2
        y2_s  = cy_s + th_s // 2
        x_end = (self._bw - r) * sc
        ac    = self._hx(ACCENT) + (255,)
        d.rounded_rectangle([r_s, y1_s, x_end, y2_s],
                            radius=th_s // 2,
                            fill=self._hx("#1a2548") + (255,))
        if cx_s > r_s:
            d.rounded_rectangle([r_s, y1_s, min(cx_s, x_end), y2_s],
                                radius=th_s // 2, fill=ac)
        img = img.resize((self._bw, self._bh), Image.LANCZOS)

        # ── Thumb at 10× (separate pass → much smoother circle) ──────────────
        tsc    = 10
        td     = r * 2 * tsc
        th_img = Image.new("RGBA", (td, td), (0, 0, 0, 0))
        th_d   = _PilDraw.Draw(th_img)
        bw_t   = tsc * 2
        th_d.ellipse([0, 0, td - 1, td - 1], fill=ac)
        th_d.ellipse([bw_t, bw_t, td - bw_t - 1, td - bw_t - 1],
                     fill=(255, 255, 255, 255))
        th_img = th_img.resize((r * 2, r * 2), Image.LANCZOS)
        img.alpha_composite(th_img, (cx - r, cy - r))

        # ── Composite against window background ───────────────────────────────
        base  = Image.new("RGBA", (self._bw, self._bh),
                          self._hx(self.cget("bg")) + (255,))
        base.alpha_composite(img)
        photo = ImageTk.PhotoImage(base.convert("RGB"))
        self._photo = photo
        self.create_image(0, 0, anchor="nw", image=photo)

    def _on_down(self, e):
        self._update(e.x)

    def _on_move(self, e):
        self._update(e.x)

    def _on_up(self, _):
        pass

    def _update(self, x):
        val = self._x_to_val(x)
        self._var.set(val)
        if self._cmd:
            self._cmd(str(val))


class PulsingDot(tk.Canvas):
    """Status dot with smooth cosine pulse animation."""
    def __init__(self, parent, color, bg=BG, size=12, **kw):
        super().__init__(parent, width=size, height=size,
                        bg=bg, highlightthickness=0, **kw)
        self._color = color
        self._bg    = bg
        self._phase = 0.0
        self.create_oval(1, 1, size-1, size-1, fill=color, outline="", tags="d")
        self._tick()

    def _blend(self, t):
        def p(c): return int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        fr, fg, fb = p(self._color)
        br, bg2, bb = p(self._bg)
        r = int(fr + (br-fr)*(1-t))
        g = int(fg + (bg2-fg)*(1-t))
        b = int(fb + (bb-fb)*(1-t))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _tick(self):
        if not self.winfo_exists():
            return
        import math
        # opacity oscillates 0.35 … 1.0 with 2 s period
        t = 0.35 + 0.65 * (1 + math.cos(self._phase * 2 * math.pi)) / 2
        self.itemconfig("d", fill=self._blend(t))
        self._phase = (self._phase + 0.025) % 1.0
        self.after(50, self._tick)

    def set_color(self, color):
        self._color = color


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.configure(bg=BG_TITLE)
        self.resizable(False, False)

        self._ser           = None
        self._ser_lock      = threading.Lock()
        self._q             = queue.Queue()
        self._cfg           = self._load_config()
        self._intensity     = self._cfg.get("intensity", 50) / 100
        self._vrc_connected = False
        self._ble_connected = False
        self._last_osc      = 0.0
        self._last_motor_nz = 0.0  # last time a non-zero motor value was sent
        self._drag_x        = 0
        self._drag_y        = 0
        self._logo_img      = None
        self._port_var       = tk.StringVar(value=self._cfg.get("port", ""))
        self._board_var      = tk.StringVar(value=self._cfg.get("dongle_board", "nicenano"))
        self._lang_var       = tk.StringVar(value=self._cfg.get("lang", "de"))
        self._settings_open     = False
        self._settings_win      = None
        self._settings_conn_btn = None
        self._osc_verbose    = bool(self._cfg.get("osc_verbose", False))
        self._vib_mode       = int(self._cfg.get("vib_mode", 0))  # 0=proximity 1=trigger
        self._console_win    = None
        self._console_text   = None
        self._log_buf        = collections.deque(maxlen=500)
        self._hp_version     = "?"
        self._dongle_version = "?"
        self._hp_ver_var     = tk.StringVar(value="?")
        self._dongle_ver_var = tk.StringVar(value="?")
        self._save_after_id  = None
        self._updates               = {}   # "headpat"|"dongle"|"server" -> {tag, url, asset, path}
        self._last_check_had_errors = False
        self._manual_uf2_path       = None
        self._pending_flash         = None
        self._known_drives   = set()
        self._badge_lbl      = None   # kept for compat
        self._badge_cvs      = None
        self._sync_img_dim   = None
        self._sync_img_on    = None
        self._pending_flash  = None

        self._int_var        = tk.DoubleVar(value=50)
        self._int_pct_var    = tk.StringVar(value="50%")
        self._bat_text       = "🔋 ?%"
        self._bat_fg         = FG_DIM

        self._load_icon()
        self._build()
        _iv = self._cfg.get("intensity", 50)
        self._int_var.set(_iv)
        self._int_pct_var.set(f"{int(_iv)}%")
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w,  h  = self.winfo_width(),       self.winfo_height()
        wx, wy = self._cfg.get("win_x"), self._cfg.get("win_y")
        if wx is not None and wy is not None and 0 <= wx < sw and 0 <= wy < sh:
            self.geometry(f"+{wx}+{wy}")
        else:
            self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
        self.after(200, self._fix_taskbar)
        self.after(100, self._apply_rounded_corners)
        self._refresh_ports()
        self._start_osc()
        self._tick()
        if self._cfg.get("auto_connect") and self._port_var.get():
            self.after(300, self._connect)
        if os.name == "posix":
            self.after(800, self._check_linux_serial_perms)
        threading.Thread(target=self._update_loop, daemon=True).start()
        threading.Thread(target=self._drive_loop,  daemon=True).start()

    # ── Update checker ───────────────────────────────────────────────────────
    def _update_loop(self):
        time.sleep(5)
        while True:
            self._check_all_releases()
            time.sleep(UPDATE_INTERVAL)

    def _check_all_releases(self):
        asset_win  = "HeadpatServer-Setup.exe"
        asset_lin  = "HeadpatServer-x86_64.AppImage"
        checks = [
            ("headpat", HEADPAT_REPO, "headpat-firmware.uf2"),
            ("server",  SERVER_REPO,  asset_win if os.name == "nt" else asset_lin),
        ]
        found_any    = False
        net_errors   = 0
        checks_done  = 0
        for key, repo, asset_name in checks:
            try:
                data   = self._gh_latest(repo)
                checks_done += 1
                tag    = data.get("tag_name", "")
                if not tag:
                    self._log(f"Update {key}: keine Version in API-Antwort", "warn")
                    continue
                assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}
                if asset_name not in assets:
                    self._log(f"Update {key}: Asset '{asset_name}' nicht in {tag}", "info")
                    continue
                existing = self._updates.get(key, {})
                if existing.get("tag") == tag:
                    found_any = True
                    continue
                if key == "server" and self._parse_ver(tag) <= self._parse_ver(SERVER_VERSION):
                    self._log(f"Server aktuell ({SERVER_VERSION}), neueste: {tag}", "info")
                    continue
                if key == "headpat" and self._hp_version != "?" and \
                        self._parse_ver(tag) <= self._parse_ver(self._hp_version):
                    continue
                self._log(f"Update {key}: {tag} verfügbar", "info")
                self._updates[key] = {"tag": tag, "url": assets[asset_name],
                                      "asset": asset_name, "path": None}
                self._q.put(("update_found", (key, tag)))
                threading.Thread(target=self._prefetch, args=(key,), daemon=True).start()
                found_any = True
            except Exception as e:
                self._log(f"Update {key}: Netzwerkfehler – {e}", "warn")
                net_errors += 1
        self._last_check_had_errors = (net_errors > 0 and checks_done == 0)
        if not found_any and checks_done > 0:
            self._log("Alle Komponenten aktuell.", "info")

    def _gh_latest(self, repo):
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": f"HeadpatServer/{SERVER_VERSION}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def _parse_ver(self, tag):
        return tuple(int(x) for x in re.findall(r'\d+', tag))

    def _recheck_firmware_updates(self):
        changed = False
        for key, cur in (("headpat", self._hp_version),):
            if key in self._updates and cur != "?":
                if self._parse_ver(self._updates[key]["tag"]) <= self._parse_ver(cur):
                    del self._updates[key]
                    changed = True
        if changed:
            self._set_badge_active(bool(self._updates))

    def _prefetch(self, key):
        entry = self._updates.get(key)
        if not entry or entry.get("path"):
            return
        try:
            if key == "server" and os.name == "nt":
                downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(downloads, exist_ok=True)
                dest = os.path.join(downloads, entry["asset"])
            else:
                suffix = os.path.splitext(entry["asset"])[1]
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp.close()
                dest = tmp.name
            req = urllib.request.Request(
                entry["url"], headers={"User-Agent": f"HeadpatServer/{SERVER_VERSION}"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
            self._updates[key]["path"] = dest
            name = {"headpat": "Headpat", "dongle": "Dongle", "server": "Server"}.get(key, key)
            self._log(f"Update bereit: {name} {entry['tag']}", "info")
        except Exception as e:
            self._log(f"Update-Download fehlgeschlagen ({key}): {e}", "warn")

    # ── Drive watcher ─────────────────────────────────────────────────────────
    def _drive_loop(self):
        while True:
            time.sleep(1.5)
            try:
                drives = self._find_nrf52_drives()
                new = drives - self._known_drives
                self._known_drives = drives
                if new:
                    self._q.put(("nrf52_drive", new))
            except Exception:
                pass

    def _find_nrf52_drives(self):
        found = set()
        if os.name == "nt":
            import ctypes, string
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:
                        buf = ctypes.create_unicode_buffer(1024)
                        try:
                            ctypes.windll.kernel32.GetVolumeInformationW(
                                drive, buf, 1024, None, None, None, None, 0)
                            if buf.value in NRF52_LABELS:
                                found.add(drive)
                        except Exception:
                            pass
                bitmask >>= 1
        else:
            import getpass
            user = getpass.getuser()
            for base in (f"/media/{user}", f"/run/media/{user}", "/media"):
                for label in NRF52_LABELS:
                    p = os.path.join(base, label)
                    if os.path.isdir(p):
                        found.add(p)
        return found

    def _pick_and_flash_uf2(self):
        path = tk_filedialog.askopenfilename(
            title="UF2-Firmware wählen",
            filetypes=[("UF2 Firmware", "*.uf2"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return
        self._manual_uf2_path = path
        # Laufwerk schon gemountet? → sofort flashen (z.B. manueller DFU vor Klick)
        existing = self._known_drives.copy()
        if existing:
            self._on_nrf52_drive(existing)
            return
        ser = self._ser
        if ser and ser.is_open:
            try:
                ser.write(b"dfu\n")
                self._log(f"Flash UF2: {os.path.basename(path)} — DFU-Befehl gesendet, warte auf Laufwerk…", "info")
                self.after(500, self._disconnect)
            except Exception as e:
                self._manual_uf2_path = None
                self._log(f"DFU-Befehl fehlgeschlagen: {e}", "err")
        else:
            self._log(f"Flash UF2: {os.path.basename(path)} — DFU-Modus manuell starten, dann Laufwerk wird erkannt…", "warn")

    def _on_nrf52_drive(self, drives):
        fw = {k: v for k, v in self._updates.items() if k in ("headpat", "dongle")}
        drive = next(iter(drives))
        self._log(f"NRF52-Laufwerk erkannt: {drive}", "info")

        # Manuell gewählte UF2-Datei hat Vorrang
        if self._manual_uf2_path and os.path.isfile(self._manual_uf2_path):
            path = self._manual_uf2_path
            self._manual_uf2_path = None
            self._pending_flash   = None
            self._log(f"Manueller Flash: {os.path.basename(path)}", "info")
            try:
                shutil.copy2(path, os.path.join(drive, os.path.basename(path)))
                self._log("Flash erfolgreich — Dongle startet neu…", "info")
                self.after(4000, self._connect)
            except Exception as e:
                self._log(f"Flash fehlgeschlagen: {e}", "err")
            return

        if not fw:
            self._log("Kein Firmware-Update verfügbar — UF2 manuell flashen?", "warn")
            return

        # Use pending flash key if set (triggered by _initiate_flash)
        if self._pending_flash and self._pending_flash in fw:
            self._flash_uf2_wait(self._pending_flash, drive)
            return

        if len(fw) == 1:
            self._flash_uf2_wait(next(iter(fw)), drive)
        else:
            win = tk.Toplevel(self)
            win.title("Firmware Update")
            win.configure(bg=BG)
            win.resizable(False, False)
            win.grab_set()
            tk.Label(win, text="Welches Gerät flashen?",
                     bg=BG, fg=FG, font=("Segoe UI", 11), pady=12).pack(padx=20)
            for key, entry in fw.items():
                name = "Headpat" if key == "headpat" else "Dongle"
                def _do(k=key, w=win, d=drive):
                    w.destroy(); self._flash_uf2_wait(k, d)
                tk.Button(win, text=f"{name}  —  {entry['tag']}", command=_do,
                          bg=BG_BTN, fg=FG, activebackground=BG_BTN_A, bd=0,
                          relief="flat", font=("Segoe UI", 11), padx=16, pady=8,
                          cursor="hand2").pack(fill="x", padx=20, pady=4)
            tk.Button(win, text="Abbrechen", command=win.destroy,
                      bg=BG_TITLE, fg=FG_DIM, activebackground=BG_BTN, bd=0,
                      relief="flat", font=("Segoe UI", 10), padx=12, pady=6,
                      cursor="hand2").pack(pady=(4, 16))

    def _flash_uf2_wait(self, key, drive):
        entry = self._updates.get(key)
        if not entry:
            return
        if entry.get("path"):
            self._flash_uf2(key, drive)
            return
        # UF2 noch nicht fertig heruntergeladen — Warte-Dialog zeigen
        win = tk.Toplevel(self)
        win.title("Herunterladen…")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()
        tk.Frame(win, bg=ACCENT, height=2).pack(fill="x")
        lbl = tk.Label(win, text=_t("downloading"),
                       bg=BG, fg=FG, font=("Segoe UI", 11), pady=16)
        lbl.pack(padx=24)
        dots = tk.Label(win, text="", bg=BG, fg=ACCENT,
                        font=("Segoe UI", 11))
        dots.pack(pady=(0, 16))

        cancelled = [False]
        def cancel():
            cancelled[0] = True
            win.destroy()
        tk.Button(win, text="Abbrechen", command=cancel,
                  bg=BG_TITLE, fg=FG_DIM, activebackground=BG_BTN,
                  bd=0, relief="flat", font=("Segoe UI", 9), padx=10, pady=4,
                  cursor="hand2").pack(pady=(0, 12))

        def poll(n=0):
            if cancelled[0]:
                return
            if not win.winfo_exists():
                return
            e = self._updates.get(key, {})
            if e.get("path"):
                win.destroy()
                self._flash_uf2(key, drive)
                return
            if e.get("path") is None and not e:
                win.destroy()
                return
            dots.config(text="●" * (n % 4 + 1))
            win.after(500, lambda: poll(n + 1))

        poll()

    def _flash_uf2(self, key, drive):
        entry = self._updates.get(key)
        if not entry or not entry.get("path"):
            return
        self._pending_flash = None
        try:
            dest = os.path.join(drive, "firmware.uf2")
            shutil.copyfile(entry["path"], dest)
            name = "Headpat" if key == "headpat" else "Dongle"
            self._log(f"{name} {entry['tag']} geflasht — Gerät bootet neu", "info")
            if key == "dongle":
                self.after(4000, self._connect)
        except Exception as e:
            tk.messagebox.showerror("Flash-Fehler", str(e), parent=self)

    def _open_update_dialog(self):
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.configure(bg=BG_TITLE)
        win.resizable(False, False)
        win.withdraw()

        _drag = [0, 0]
        def _drag_start(e):
            _drag[0] = e.x_root - win.winfo_x()
            _drag[1] = e.y_root - win.winfo_y()
        def _drag_move(e):
            win.geometry(f"+{e.x_root - _drag[0]}+{e.y_root - _drag[1]}")

        # ── Titlebar ──────────────────────────────────────────────────────
        tb = tk.Frame(win, bg=BG_TITLE, height=44)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tb.bind("<ButtonPress-1>", _drag_start)
        tb.bind("<B1-Motion>",     _drag_move)

        dot = tk.Canvas(tb, width=9, height=9, bg=BG_TITLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=ACCENT, outline="")
        dot.pack(side="left", padx=(14, 7), pady=18)
        dot.bind("<ButtonPress-1>", _drag_start)
        dot.bind("<B1-Motion>",     _drag_move)

        title_lbl = tk.Label(tb, text="Updates", bg=BG_TITLE, fg=FG,
                             font=("Inter", 11, "bold"))
        title_lbl.pack(side="left")
        title_lbl.bind("<ButtonPress-1>", _drag_start)
        title_lbl.bind("<B1-Motion>",     _drag_move)

        RoundedBtn(tb, "✕", win.destroy,
                   w=28, h=28, r=7, font_size=13,
                   fill=BG_TITLE, fg=FG_DIM,
                   hover="#452525", hover_fg=RED,
                   press="#5a2525", p_bg=BG_TITLE
                   ).pack(side="right", padx=(0, 6), pady=8)

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        head = tk.Frame(body, bg=BG)
        head.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(head, text=_t("upd_available"), bg=BG, fg=FG,
                 font=("Inter", 11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(head, text=_t("upd_usb_hint"), bg=BG, fg=FG_DIM,
                 font=("Inter", 9), justify="left", anchor="w").pack(anchor="w", pady=(3, 0))

        labels = {"headpat": "Headpat Firmware", "dongle": "Dongle Firmware", "server": "Server"}
        if self._updates:
            for key, entry in self._updates.items():
                tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20)
                row = tk.Frame(body, bg=BG)
                row.pack(fill="x", padx=20, pady=10)

                info = tk.Frame(row, bg=BG)
                info.pack(side="left")
                tk.Label(info, text=entry["tag"], bg=BG, fg=ACCENT,
                         font=("Inter", 10, "bold")).pack(side="left", padx=(0, 8))
                tk.Label(info, text=labels.get(key, key), bg=BG, fg=FG,
                         font=("Inter", 10, "bold")).pack(side="left")

                if key == "server":
                    cmd = lambda k=key, w=win: (w.destroy(), self._server_update(k))
                    lbl = _t("btn_update")
                else:
                    cmd = lambda k=key, w=win: self._initiate_flash(k, w)
                    lbl = _t("btn_flash")
                RoundedBtn(row, lbl, cmd,
                           w=92, h=30, r=8, p_bg=BG,
                           fill=ACCENT, fg="#ffffff",
                           hover="#5591ff", hover_fg="#ffffff",
                           font_spec=("Inter", 10, "bold")
                           ).pack(side="right")
        else:
            if self._last_check_had_errors:
                tk.Label(body, text="GitHub nicht erreichbar.\nDetails im Terminal.", bg=BG,
                         fg=YELLOW, font=("Inter", 10), justify="center", pady=14).pack()
            else:
                tk.Label(body, text=_t("upd_all_ok"), bg=BG, fg=FG_DIM,
                         font=("Inter", 10), pady=14).pack()

        # ── Bottom ────────────────────────────────────────────────────────
        def _refresh():
            win.destroy()
            self._log("Suche nach Updates…", "info")
            def _run():
                self._check_all_releases()
                self.after(0, self._open_update_dialog)
            threading.Thread(target=_run, daemon=True).start()

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x")
        bottom = tk.Frame(body, bg=BG)
        bottom.pack(fill="x", padx=20, pady=(12, 16))
        RoundedBtn(bottom, _t("btn_refresh"), _refresh,
                   w=130, h=34, r=9, p_bg=BG,
                   fill=ACCENT, fg="#ffffff",
                   hover="#5591ff", hover_fg="#ffffff",
                   font_spec=("Inter", 11, "bold")
                   ).pack(side="left")
        RoundedBtn(bottom, _t("btn_close"), win.destroy,
                   w=100, h=34, r=9, p_bg=BG,
                   fill=BG_BTN, fg=FG_DIM,
                   hover=BG_BTN_A, hover_fg=FG,
                   border_col=BORDER,
                   font_spec=("Inter", 11)
                   ).pack(side="right")

        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        win.geometry(f"+{x}+{y}")
        win.deiconify()
        self.after(0, lambda: self._round_toplevel(win))

    def _initiate_flash(self, key, dialog=None):
        if dialog:
            dialog.destroy()
        entry = self._updates.get(key)
        if not entry:
            return
        if not entry.get("path"):
            tk.messagebox.showinfo("Bitte warten",
                                   "Download läuft noch, kurz warten und nochmal versuchen.",
                                   parent=self)
            return

        self._open_headpat_flash_dialog()

    def _open_headpat_flash_dialog(self):
        win = tk.Toplevel(self)
        win.title(_t("hp_flash_title"))
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()
        tk.Frame(win, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(win, text=_t("hp_flash_title"), bg=BG, fg=FG,
                 font=("Segoe UI", 12, "bold"), pady=12).pack(padx=20)
        tk.Label(win, text=_t("hp_flash_hint"),
                 bg=BG, fg=FG_DIM, font=("Segoe UI", 10), justify="center").pack(padx=20, pady=(0, 14))

        port_row = tk.Frame(win, bg=BG)
        port_row.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(port_row, text="COM Port:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 10)).pack(side="left")

        ports = [p.device for p in serial.tools.list_ports.comports()] if SERIAL_OK else []
        port_var = tk.StringVar()
        port_combo = ttk.Combobox(port_row, textvariable=port_var, values=ports,
                                  width=10, style="P.TCombobox")
        port_combo.pack(side="left", padx=(8, 0))

        status_lbl = tk.Label(win, text="", bg=BG, fg=FG_DIM, font=("Segoe UI", 9))
        status_lbl.pack(pady=(0, 10))

        def _search():
            status_lbl.config(text="Suche…", fg=YELLOW)
            win.update()
            def _run():
                port = self._auto_find_headpat_port()
                def _done():
                    if not win.winfo_exists():
                        return
                    if port:
                        port_var.set(port)
                        status_lbl.config(text=f"Headpat gefunden: {port}", fg=GREEN)
                    else:
                        status_lbl.config(text="Kein Headpat gefunden", fg=FG_DIM)
                win.after(0, _done)
            threading.Thread(target=_run, daemon=True).start()

        tk.Button(port_row, text=_t("btn_search"), command=_search,
                  bg=BG_BTN, fg=FG_DIM, activebackground=BG_BTN_A, bd=0,
                  relief="flat", font=("Segoe UI", 10), padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(6, 0))

        def _do_flash():
            port = port_var.get()
            if not port:
                return
            win.destroy()
            self._pending_flash = "headpat"
            threading.Thread(target=self._trigger_headpat_dfu, args=(port,), daemon=True).start()

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(4, 16))
        tk.Button(btn_row, text=_t("btn_cancel"), command=win.destroy,
                  bg=BG_TITLE, fg=FG_DIM, activebackground=BG_BTN, bd=0,
                  relief="flat", font=("Segoe UI", 10), padx=12, pady=6,
                  cursor="hand2").pack(side="left")
        tk.Button(btn_row, text=_t("btn_flash"), command=_do_flash,
                  bg=BG_BTN, fg=ACCENT, activebackground=BG_BTN_A, bd=0,
                  relief="flat", font=("Segoe UI", 10), padx=12, pady=6,
                  cursor="hand2").pack(side="right")

    def _auto_find_headpat_port(self):
        if not SERIAL_OK:
            return None
        for info in serial.tools.list_ports.comports():
            port = info.device
            try:
                with serial.Serial(port, BAUD, timeout=1) as s:
                    time.sleep(0.1)
                    s.reset_input_buffer()
                    s.write(b"info\n")
                    data = b""
                    deadline = time.time() + 1.2
                    while time.time() < deadline:
                        if s.in_waiting:
                            data += s.read(s.in_waiting)
                        if b"Headpat v" in data:
                            return port
                        time.sleep(0.05)
            except Exception:
                pass
        return None

    def _trigger_headpat_dfu(self, port):
        try:
            with serial.Serial(port, BAUD, timeout=1) as s:
                time.sleep(0.1)
                s.write(b"dfu\n")
                time.sleep(0.3)
            self._log(f"[HEADPAT] DFU gesendet an {port}, warte auf Laufwerk…", "info")
        except Exception as e:
            self._log(f"[HEADPAT] DFU-Fehler: {e}", "err")

    def _server_update(self, key):
        entry = self._updates.get(key)
        if not entry or not entry.get("path"):
            tk.messagebox.showinfo("Bitte warten", "Download läuft noch…", parent=self)
            return
        import subprocess
        src = entry["path"]
        if os.name == "nt":
            import ctypes
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "open", src, None, None, 1)
                self.after(1500, lambda: os._exit(0))
            except Exception as e:
                tk.messagebox.showerror("Update-Fehler", str(e), parent=self)
                return
        else:
            os.chmod(src, 0o755)
            subprocess.Popen([src])
            self.after(3000, self._on_close)

    # ── Taskbar icon ──────────────────────────────────────────────────────────
    def _fix_taskbar(self):
        if os.name != "nt":
            return
        import ctypes
        # GA_ROOT=2 liefert den echten Top-Level-HWND (winfo_id gibt nur das Tk-Child zurück)
        hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
        GWL_EXSTYLE      = -20
        WS_EX_APPWINDOW  = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        SWP_NOMOVE       = 0x0002
        SWP_NOSIZE       = 0x0001
        SWP_NOZORDER     = 0x0004
        SWP_FRAMECHANGED = 0x0020
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )
        self.wm_withdraw()
        self.after(50, self.wm_deiconify)

    def _apply_rounded_corners(self):
        if os.name != "nt":
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
            # DWMWA_WINDOW_CORNER_PREFERENCE=33, DWMWCP_ROUND=2 (Windows 11)
            val = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

    def _round_toplevel(self, widget):
        if os.name != "nt":
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetAncestor(widget.winfo_id(), 2)
            val  = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

    # ── Linux serial port permissions ────────────────────────────────────────
    def _check_linux_serial_perms(self):
        udev_rule = "/etc/udev/rules.d/99-headpat.rules"
        if os.path.exists(udev_rule):
            return
        import grp, subprocess
        try:
            in_dialout = grp.getgrnam("dialout").gr_gid in os.getgroups()
        except KeyError:
            in_dialout = False
        if in_dialout:
            return
        if not tk.messagebox.askyesno(
            "Serieller Port",
            "Für den Dongle wird eine udev-Regel benötigt.\n\n"
            "Jetzt einrichten? (Einmalig, erfordert Admin-Passwort)\n\n"
            "Danach den Dongle neu einstecken.",
            parent=self
        ):
            return
        rule = 'SUBSYSTEM=="tty", ATTRS{idVendor}=="239a", TAG+="uaccess"\n'
        try:
            result = subprocess.run(
                ["pkexec", "sh", "-c",
                 f"tee {udev_rule} && udevadm control --reload-rules && udevadm trigger"],
                input=rule.encode(), capture_output=True
            )
            if result.returncode == 0:
                tk.messagebox.showinfo(
                    "Fertig",
                    "udev-Regel eingerichtet.\nBitte den Dongle neu einstecken.",
                    parent=self
                )
            else:
                tk.messagebox.showerror("Fehler", "Konnte udev-Regel nicht erstellen.", parent=self)
        except FileNotFoundError:
            tk.messagebox.showerror(
                "Fehler",
                "pkexec nicht gefunden.\nFühre manuell aus:\n"
                f'echo \'{rule.strip()}\' | sudo tee {udev_rule}\n'
                "sudo udevadm control --reload-rules && sudo udevadm trigger",
                parent=self
            )

    # ── Config persistence ───────────────────────────────────────────────────
    def _load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        cfg = {
            "port":          self._port_var.get(),
            "intensity":     self._int_var.get(),
            "osc_verbose":   self._osc_verbose,
            "auto_connect":  self._ser is not None,
            "win_x":         self.winfo_x(),
            "win_y":         self.winfo_y(),
            "dongle_board":  self._board_var.get(),
            "lang":          self._lang_var.get(),
            "vib_mode":      self._vib_mode,
        }
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _debounce_save(self):
        if self._save_after_id:
            self.after_cancel(self._save_after_id)
        self._save_after_id = self.after(800, self._save_config)

    def _on_close(self):
        self._save_config()
        self.destroy()

    # ── Icon ──────────────────────────────────────────────────────────────────
    def _load_icon(self):
        if not (PIL_OK and os.path.exists(ICON_PATH)):
            return
        try:
            img = Image.open(ICON_PATH).convert("RGBA")
            self._logo_img = ImageTk.PhotoImage(img.resize((20, 20), Image.LANCZOS))
            big = ImageTk.PhotoImage(img.resize((64, 64), Image.LANCZOS))
            self.wm_iconphoto(True, big)
            self._big_icon = big
        except Exception:
            pass

    # ── Sync icon ─────────────────────────────────────────────────────────────
    def _render_sync_icon(self, size=18, active=True):
        """Draw a circular-arrows refresh icon. Returns PhotoImage or None."""
        if not PIL_OK:
            return None
        import math
        sc = 5
        s  = size * sc
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d   = _PilDraw.Draw(img)

        h   = (ACCENT if active else FG_DIM).lstrip('#')
        col = tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255 if active else 70,)

        cx = cy = s / 2
        r  = s * 0.37
        lw = max(int(s * 0.15), 2)
        bb = [cx - r, cy - r, cx + r, cy + r]
        g  = 22  # gap in degrees at each arrowhead

        # Arc 1: right+bottom half (300° → 98° clockwise, through east & south)
        d.arc(bb, start=300 + g, end=120 - g, fill=col, width=lw)
        # Arc 2: left+top half  (142° → 278° clockwise, through west & north)
        d.arc(bb, start=120 + g, end=300 - g, fill=col, width=lw)

        def arrowhead(angle_deg):
            a   = math.radians(angle_deg)
            tx  = cx + r * math.cos(a)
            ty  = cy + r * math.sin(a)
            Tx, Ty = -math.sin(a), math.cos(a)   # clockwise tangent
            hw  = lw * 1.1
            dep = lw * 1.3
            p1  = (tx + hw * math.cos(a) - dep * Tx,
                   ty + hw * math.sin(a) - dep * Ty)
            p2  = (tx - hw * math.cos(a) - dep * Tx,
                   ty - hw * math.sin(a) - dep * Ty)
            p3  = (tx + lw * 0.4 * Tx, ty + lw * 0.4 * Ty)
            d.polygon([p1, p2, p3], fill=col)

        arrowhead(120 - g)   # end of arc 1
        arrowhead(300 - g)   # end of arc 2

        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _render_gear_icon(self, size=15, active=True):
        """Draw an 8-tooth gear icon with center hole. Returns PhotoImage or None."""
        if not PIL_OK:
            return None
        import math
        sc = 5
        s  = size * sc

        h   = (FG if active else FG_DIM).lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        av  = 255 if active else 70

        cx = cy = s / 2
        N      = 8
        r_out  = s * 0.46     # tooth tip radius
        r_in   = s * 0.315    # tooth base / body radius
        r_hole = s * 0.135    # center hole radius
        tfrac  = 0.42         # tooth width as fraction of one slot
        offset = -math.pi / 2  # first tooth points straight up

        # Build polygon: tooth vertices + arc points along body between teeth
        pts = []
        for i in range(N):
            a0  = offset + 2 * math.pi * i / N
            a1  = offset + 2 * math.pi * (i + 1) / N
            mid = (a0 + a1) / 2
            hw  = (a1 - a0) * tfrac / 2
            # Left base → left tip → right tip → right base
            pts.append((cx + r_in  * math.cos(mid - hw),       cy + r_in  * math.sin(mid - hw)))
            pts.append((cx + r_out * math.cos(mid - hw * 0.7), cy + r_out * math.sin(mid - hw * 0.7)))
            pts.append((cx + r_out * math.cos(mid + hw * 0.7), cy + r_out * math.sin(mid + hw * 0.7)))
            pts.append((cx + r_in  * math.cos(mid + hw),       cy + r_in  * math.sin(mid + hw)))
            # Smooth arc along body between this tooth and the next
            for j in range(1, 4):
                aa = mid + hw + (2 * math.pi / N * (1 - tfrac)) * j / 3
                pts.append((cx + r_in * math.cos(aa), cy + r_in * math.sin(aa)))

        # Build alpha mask: gear shape + body fill, then erase center hole
        mask = Image.new("L", (s, s), 0)
        md   = _PilDraw.Draw(mask)
        md.polygon(pts, fill=255)
        md.ellipse([cx - r_in,   cy - r_in,   cx + r_in,   cy + r_in],   fill=255)
        md.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill=0)

        if av < 255:
            mask = mask.point(lambda p: p * av // 255)

        img = Image.new("RGBA", (s, s), rgb + (255,))
        img.putalpha(mask)
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _render_terminal_icon(self, size=15, active=True):
        """Draw a '>_' terminal icon inside a rounded square. Returns PhotoImage or None."""
        if not PIL_OK:
            return None
        import math
        sc = 5
        s  = size * sc
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d   = _PilDraw.Draw(img)

        h   = (FG if active else FG_DIM).lstrip('#')
        col = tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255 if active else 70,)

        lw     = max(int(s * 0.09), 2)
        margin = int(s * 0.04)
        radius = int(s * 0.23)

        # Rounded square outline
        d.rounded_rectangle([margin, margin, s - margin - 1, s - margin - 1],
                            radius=radius, outline=col, width=lw)

        # ">" chevron — left-center
        cx   = s * 0.30
        cy   = s * 0.50
        arm  = s * 0.15
        tip  = cx + arm * 0.9
        lw2  = max(int(lw * 1.05), 2)
        d.line([(cx, cy - arm), (tip, cy)], fill=col, width=lw2)
        d.line([(cx, cy + arm), (tip, cy)], fill=col, width=lw2)

        # "—" cursor line — to the right of ">"
        x1 = tip + s * 0.06
        x2 = s * 0.76
        y  = cy + arm * 0.35
        d.line([(x1, y), (x2, y)], fill=col, width=lw2)

        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _set_badge_active(self, active: bool):
        if self._badge_cvs is None:
            return
        if PIL_OK and self._sync_img_on:
            img = self._sync_img_on if active else self._sync_img_dim
            self._badge_cvs.itemconfig("icon", image=img)
        else:
            self._badge_cvs.itemconfig("icon", fill=ACCENT if active else FG_DIM)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        # ── Title bar ─────────────────────────────────────────────────────────
        tb = tk.Frame(self, bg=BG_TITLE, height=44)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        for w in (tb,):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

        dot = tk.Canvas(tb, width=9, height=9, bg=BG_TITLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=ACCENT, outline="")
        dot.pack(side="left", padx=(14, 7), pady=18)
        dot.bind("<ButtonPress-1>", self._drag_start)
        dot.bind("<B1-Motion>",     self._drag_move)

        name_lbl = tk.Label(tb, text="Headpat Server",
                            bg=BG_TITLE, fg=FG, font=("Inter", 13, "bold"))
        name_lbl.pack(side="left", pady=10)
        name_lbl.bind("<ButtonPress-1>", self._drag_start)
        name_lbl.bind("<B1-Motion>",     self._drag_move)

        ver_lbl = tk.Label(tb, text=SERVER_VERSION,
                           bg=BG_TITLE, fg=FG_DIM, font=("Inter", 11))
        ver_lbl.pack(side="left", padx=(5, 0), pady=10)
        ver_lbl.bind("<ButtonPress-1>", self._drag_start)
        ver_lbl.bind("<B1-Motion>",     self._drag_move)

        RoundedBtn(tb, "✕", self._on_close,
                   w=28, h=28, r=7, font_size=13,
                   fill=BG_TITLE, fg=FG_DIM,
                   hover="#452525", hover_fg=RED,
                   press="#5a2525", p_bg=BG_TITLE
                   ).pack(side="right", padx=(0, 6), pady=8)

        try:
            _gear_dim = self._render_gear_icon(15, active=False)
            _gear_on  = self._render_gear_icon(15, active=True)
        except Exception:
            _gear_dim = _gear_on = None
        RoundedBtn(tb, "⚙", self._open_settings,
                   w=28, h=28, r=7, font_size=13,
                   fill=BG_TITLE, fg=FG_DIM,
                   hover="#2c3a58", hover_fg=FG,
                   press="#2c3a58", p_bg=BG_TITLE,
                   img_normal=_gear_dim, img_hover=_gear_on
                   ).pack(side="right", padx=2, pady=8)

        # ── Update button (always visible; gray=aktuell, blue=update) ───────────
        try:
            self._sync_img_dim = self._render_sync_icon(17, active=False)
            self._sync_img_on  = self._render_sync_icon(17, active=True)
        except Exception:
            self._sync_img_dim = self._sync_img_on = None
        bsz = 28
        self._badge_cvs = tk.Canvas(tb, width=bsz, height=bsz,
                                    bg=BG_TITLE, highlightthickness=0, cursor="hand2")
        self._badge_cvs.pack(side="right", padx=2, pady=8)
        if PIL_OK and self._sync_img_dim:
            self._badge_cvs.create_image(bsz // 2, bsz // 2,
                                         image=self._sync_img_dim,
                                         anchor="center", tags="icon")
        else:
            self._badge_cvs.create_text(bsz // 2, bsz // 2, text="↺",
                                        fill=FG_DIM, font=("Segoe UI", 14),
                                        tags="icon")
        self._badge_cvs.bind("<Button-1>", lambda _: self._open_update_dialog())
        self._badge_lbl = self._badge_cvs   # compat alias

        try:
            _term_dim = self._render_terminal_icon(15, active=False)
            _term_on  = self._render_terminal_icon(15, active=True)
        except Exception:
            _term_dim = _term_on = None
        self._log_btn = RoundedBtn(tb, "≡", self._toggle_console,
                                   w=28, h=28, r=7, font_size=15,
                                   fill=BG_TITLE, fg=FG_DIM,
                                   hover="#2c3a58", hover_fg=FG,
                                   press="#2c3a58", p_bg=BG_TITLE,
                                   img_normal=_term_dim, img_hover=_term_on)
        self._log_btn.pack(side="right", padx=2, pady=8)


        self._build_main_card()

    def _build_main_card(self):
        fl = 11
        fp = 12

        card = tk.Frame(self, bg=BG)
        card.pack(fill="both", expand=True)
        self._main_card = card

        # ── Status row ────────────────────────────────────────────────────────
        status = tk.Frame(card, bg=BG)
        status.pack(fill="x", padx=20, pady=(14, 10))

        self._hp_dot = self._dot(status, GREEN if self._ble_connected else RED)
        self._hp_dot.pack(side="left")
        tk.Label(status, text="Headpat", bg=BG, fg=FG,
                 font=("Inter", fl, "bold")).pack(side="left", padx=(6, 0))

        self._vrc_dot = self._dot(status, GREEN if self._vrc_connected else RED)
        self._vrc_dot.pack(side="left", padx=(18, 0))
        tk.Label(status, text="OSC", bg=BG, fg=FG,
                 font=("Inter", fl, "bold")).pack(side="left", padx=(6, 0))

        self._bat_lbl = tk.Label(status, text=self._bat_text, bg=BG,
                                 fg=self._bat_fg, font=("JetBrains Mono", fp))
        self._bat_lbl.pack(side="right")

        # ── Intensity label + % ───────────────────────────────────────────────
        int_label_row = tk.Frame(card, bg=BG)
        int_label_row.pack(fill="x", padx=20, pady=(10, 2))
        tk.Label(int_label_row, text="Intensität", bg=BG, fg=FG,
                 font=("Inter", fl, "bold")).pack(side="left")
        tk.Label(int_label_row, textvariable=self._int_pct_var, bg=BG, fg=ACCENT,
                 font=("JetBrains Mono", fp, "bold")).pack(side="right")

        # ── Slider ────────────────────────────────────────────────────────────
        FancySlider(card, variable=self._int_var, from_=0, to=100,
                    command=self._on_intensity_change,
                    track_h=4, thumb_r=6, p_bg=BG
                    ).pack(fill="x", padx=16, pady=(0, 8))

        # ── Mode row ──────────────────────────────────────────────────────────
        mode_row = tk.Frame(card, bg=BG)
        mode_row.pack(fill="x", padx=20, pady=(8, 8))
        tk.Label(mode_row, text="Modus", bg=BG, fg=FG,
                 font=("Inter", fl, "bold")).pack(side="left")

        def _select_mode(m):
            self._vib_mode = m
            self._debounce_save()

        seg = SegmentedControl(mode_row, ["Proximity", "Trigger"],
                               command=_select_mode,
                               active=self._vib_mode,
                               seg_w=84, h=26, r_cont=7, r_seg=6, pad=3, p_bg=BG)
        seg.pack(side="right")

        # ── Test row ──────────────────────────────────────────────────────────
        test_row = tk.Frame(card, bg=BG)
        test_row.pack(fill="x", padx=20, pady=(8, 14))
        tk.Label(test_row, text="Test", bg=BG, fg=FG,
                 font=("Inter", fl, "bold")).pack(side="left")
        self._mkbtn(test_row, "R", self._pat_right).pack(side="right")
        self._mkbtn(test_row, "L", self._pat_left).pack(side="right", padx=(0, 10))



    # ── Helpers ───────────────────────────────────────────────────────────────
    def _dot(self, parent, color):
        return PulsingDot(parent, color, bg=BG)

    def _set_dot(self, canvas, color):
        canvas.set_color(color)

    def _on_intensity_change(self, v):
        self._intensity = float(v) / 100
        self._int_pct_var.set(f"{int(float(v))}%")
        self._debounce_save()

    def _mkbtn(self, parent, text, cmd):
        return RoundedBtn(parent, text, cmd,
                          w=50, h=36, r=8, p_bg=BG,
                          fill=BG_BTN, fg=FG,
                          hover=BG_BTN, hover_fg=FG,
                          press=ACCENT, border_col=BORDER,
                          font_spec=("Inter", 11, "bold"))

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x_root - self.winfo_x()
        self._drag_y = e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── Internal log ──────────────────────────────────────────────────────────
    def _log(self, text: str, tag: str = "info"):
        ts = time.strftime("%H:%M:%S")
        entry = (ts, tag, text)
        self._log_buf.append(entry)
        self._q.put(("log", entry))

    # ── Console window ────────────────────────────────────────────────────────
    def _toggle_console(self):
        if self._console_win and self._console_win.winfo_exists():
            self._console_win.destroy()
            self._console_win = None
            self._log_btn.set_style(BG_TITLE, FG_DIM, hover="#2c3a58")
        else:
            self._open_console()

    def _open_console(self):
        win = tk.Toplevel(self)
        self._console_win = win
        win.overrideredirect(True)
        win.configure(bg=BG_TITLE)
        win.resizable(False, False)
        win.withdraw()

        _drag = [0, 0]
        def _drag_start(e):
            _drag[0] = e.x_root - win.winfo_x()
            _drag[1] = e.y_root - win.winfo_y()
        def _drag_move(e):
            win.geometry(f"+{e.x_root - _drag[0]}+{e.y_root - _drag[1]}")
        def _bind_drag(w):
            w.bind("<ButtonPress-1>", _drag_start)
            w.bind("<B1-Motion>",     _drag_move)

        # ── Titlebar ──────────────────────────────────────────────────────
        tb = tk.Frame(win, bg=BG_TITLE, height=44)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        _bind_drag(tb)

        dot = tk.Canvas(tb, width=9, height=9, bg=BG_TITLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=GREEN, outline="")
        dot.pack(side="left", padx=(14, 7), pady=18)
        _bind_drag(dot)

        title_lbl = tk.Label(tb, text="Terminal", bg=BG_TITLE, fg=FG,
                             font=("Inter", 11, "bold"))
        title_lbl.pack(side="left")
        _bind_drag(title_lbl)

        RoundedBtn(tb, "✕", self._toggle_console,
                   w=28, h=28, r=7, font_size=13,
                   fill=BG_TITLE, fg=FG_DIM,
                   hover="#452525", hover_fg=RED,
                   press="#5a2525", p_bg=BG_TITLE
                   ).pack(side="right", padx=(0, 6), pady=8)

        # OSC-Verbose + Clear log in der Titlebar
        osc_text = "OSC: alle" if self._osc_verbose else "OSC: nur Headpat"
        osc_fg   = YELLOW      if self._osc_verbose else FG_DIM
        self._verb_btn = RoundedBtn(tb, osc_text, self._toggle_verbose,
                                    w=110, h=26, r=6,
                                    fill=BG_BTN, fg=osc_fg,
                                    hover=BG_BTN_A, hover_fg=FG,
                                    border_col=BORDER,
                                    font_spec=("Inter", 9),
                                    p_bg=BG_TITLE)
        self._verb_btn.pack(side="right", padx=(0, 4), pady=9)

        RoundedBtn(tb, "Log löschen", self._clear_console,
                   w=84, h=26, r=6,
                   fill=BG_BTN, fg=FG_DIM,
                   hover=BG_BTN_A, hover_fg=FG,
                   border_col=BORDER,
                   font_spec=("Inter", 9),
                   p_bg=BG_TITLE
                   ).pack(side="right", padx=(0, 4), pady=9)

        # ── Log-Bereich ───────────────────────────────────────────────────
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        txt_frame = tk.Frame(body, bg="#07090e")
        txt_frame.pack(fill="both", expand=True)

        self._console_text = tk.Text(
            txt_frame, bg="#07090e", fg=FG_DIM,
            font=("JetBrains Mono", 9), state="disabled",
            wrap="none", selectbackground=BG_BTN_A,
            relief="flat", bd=0, insertbackground=FG
        )
        self._console_text.tag_config("PASS",   foreground=GREEN)
        self._console_text.tag_config("skip",   foreground=FG_DIM)
        self._console_text.tag_config("osc",    foreground=OSC_COL)
        self._console_text.tag_config("info",   foreground=ACCENT)
        self._console_text.tag_config("warn",   foreground=YELLOW)
        self._console_text.tag_config("err",    foreground=RED)
        self._console_text.tag_config("serial", foreground="#5a8a6a")

        vsb = tk.Scrollbar(txt_frame, orient="vertical",
                           command=self._console_text.yview,
                           bg=BG, activebackground=BG_BTN, troughcolor=BG)
        hsb = tk.Scrollbar(txt_frame, orient="horizontal",
                           command=self._console_text.xview,
                           bg=BG, activebackground=BG_BTN, troughcolor=BG)
        self._console_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._console_text.pack(side="left", fill="both", expand=True)

        self._console_text.config(state="normal")
        for ts, tag, text in self._log_buf:
            self._console_text.insert("end", f"{ts}  {text}\n", tag)
        self._console_text.see("end")
        self._console_text.config(state="disabled")

        # ── Dongle-Befehle ────────────────────────────────────────────────
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x")
        cmd_area = tk.Frame(body, bg=BG)
        cmd_area.pack(fill="x", padx=16, pady=10)

        tk.Label(cmd_area, text="DONGLE", bg=BG, fg=FG_DIM,
                 font=("Inter", 8, "bold")).pack(anchor="w", pady=(0, 6))

        CW = 78  # command button width

        for pairs in [
            [("Pairing", "pair",   ACCENT), ("List",   "list",   FG),
             ("Uptime",  "uptime", FG),     ("Remove", "remove", YELLOW),
             ("Reboot",  "reboot", FG_DIM)],
        ]:
            row = tk.Frame(cmd_area, bg=BG)
            row.pack(fill="x", pady=(0, 6))
            for text, cmd, color in pairs:
                RoundedBtn(row, text, lambda c=cmd: self._send_cmd(c),
                           w=CW, h=30, r=7, p_bg=BG,
                           fill=BG_BTN, fg=color, hover=BG_BTN_A, hover_fg=FG,
                           border_col=BORDER, font_spec=("Inter", 10, "bold")
                           ).pack(side="left", padx=(0, 6))

        dfu_row = tk.Frame(cmd_area, bg=BG)
        dfu_row.pack(fill="x")
        RoundedBtn(dfu_row, "Clear BLE", lambda: self._send_cmd("clear"),
                   w=CW, h=30, r=7, p_bg=BG,
                   fill=BG_BTN, fg=RED, hover=BG_BTN_A, hover_fg=RED,
                   border_col=BORDER, font_spec=("Inter", 10, "bold")
                   ).pack(side="left", padx=(0, 6))
        RoundedBtn(dfu_row, "DFU", lambda: self._send_cmd("dfu"),
                   w=CW, h=30, r=7, p_bg=BG,
                   fill=BG_BTN, fg=FG_DIM, hover=BG_BTN_A, hover_fg=FG,
                   border_col=BORDER, font_spec=("Inter", 10, "bold")
                   ).pack(side="left", padx=(0, 6))
        RoundedBtn(dfu_row, "Flash UF2…", self._pick_and_flash_uf2,
                   w=CW, h=30, r=7, p_bg=BG,
                   fill=BG_BTN, fg=YELLOW, hover=BG_BTN_A, hover_fg=YELLOW,
                   border_col=BORDER, font_spec=("Inter", 10, "bold")
                   ).pack(side="left")

        # ── Position & Anzeige ────────────────────────────────────────────
        win.update_idletasks()
        rw = 460
        rh = win.winfo_reqheight() + 160   # Platz für Log-Bereich
        self.update_idletasks()
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height() + 8
        win.geometry(f"{rw}x{rh}+{x}+{y}")
        win.deiconify()
        self.after(0, lambda: self._round_toplevel(win))
        self._log_btn.set_style(BG_TITLE, GREEN, hover="#2c3a58")

    def _toggle_verbose(self):
        self._osc_verbose = not self._osc_verbose
        if self._osc_verbose:
            self._log("OSC verbose ON — zeige alle Parameter", "warn")
        else:
            self._log("OSC verbose OFF", "info")
        if self._verb_btn and self._verb_btn.winfo_exists():
            new_text = "OSC: alle"      if self._osc_verbose else "OSC: nur Headpat"
            new_fg   = YELLOW           if self._osc_verbose else FG_DIM
            self._verb_btn._text = new_text
            self._verb_btn._fg   = new_fg
            self._verb_btn._draw(self._verb_btn._fill, new_fg)
        self._save_config()

    def _clear_console(self):
        if self._console_text:
            self._console_text.config(state="normal")
            self._console_text.delete("1.0", "end")
            self._console_text.config(state="disabled")
        self._log_buf.clear()

    # ── Settings window ───────────────────────────────────────────────────────
    def _send_cmd(self, cmd: str):
        with self._ser_lock:
            ser = self._ser
        if ser:
            try:
                ser.write(f"{cmd}\n".encode())
                self._log(f">>> {cmd}", "info")
            except Exception as e:
                self._log(f"Fehler: {e}", "err")
        else:
            self._log("Dongle nicht verbunden", "warn")

    def _on_board_change(self):
        self._updates.pop("dongle", None)
        self._save_config()
        threading.Thread(target=self._check_all_releases, daemon=True).start()

    def _open_settings(self, event=None):
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return
        self._settings_open = True

        win = tk.Toplevel(self)
        self._settings_win = win
        win.overrideredirect(True)
        win.configure(bg=BG_TITLE)
        win.resizable(False, False)
        win.withdraw()

        _drag = [0, 0]
        def _drag_start(e):
            _drag[0] = e.x_root - win.winfo_x()
            _drag[1] = e.y_root - win.winfo_y()
        def _drag_move(e):
            win.geometry(f"+{e.x_root - _drag[0]}+{e.y_root - _drag[1]}")
        def _bind_drag(w):
            w.bind("<ButtonPress-1>", _drag_start)
            w.bind("<B1-Motion>",     _drag_move)

        # ── Titlebar ──────────────────────────────────────────────────────
        tb = tk.Frame(win, bg=BG_TITLE, height=44)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        _bind_drag(tb)

        dot = tk.Canvas(tb, width=9, height=9, bg=BG_TITLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=ACCENT, outline="")
        dot.pack(side="left", padx=(14, 7), pady=18)
        _bind_drag(dot)

        title_lbl = tk.Label(tb, text=_t("settings_title"), bg=BG_TITLE, fg=FG,
                             font=("Inter", 11, "bold"))
        title_lbl.pack(side="left")
        _bind_drag(title_lbl)

        RoundedBtn(tb, "✕", self._close_settings,
                   w=28, h=28, r=7, font_size=13,
                   fill=BG_TITLE, fg=FG_DIM,
                   hover="#452525", hover_fg=RED,
                   press="#5a2525", p_bg=BG_TITLE
                   ).pack(side="right", padx=(0, 6), pady=8)

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        W = 300

        tk.Label(body, text=_t("settings_title"), bg=BG, fg=FG,
                 font=("Inter", 15, "bold")).pack(anchor="w", padx=20, pady=(16, 14))

        def sep(): tk.Frame(body, bg=BORDER, height=1).pack(fill="x")
        def sec(t): tk.Label(body, text=t.upper(), bg=BG, fg=FG_DIM,
                             font=("Inter", 8, "bold")).pack(anchor="w", padx=20, pady=(10, 6))

        # Combobox style
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("P.TCombobox", fieldbackground=BG_BTN, background=BG_BTN,
                    foreground=FG, selectbackground=BG_BTN_A,
                    selectforeground=FG, arrowcolor=ACCENT, bordercolor=BORDER,
                    insertcolor=FG)
        s.map("P.TCombobox",
              fieldbackground=[("focus", BG_BTN), ("!focus", BG_BTN)],
              foreground=[("focus", FG), ("!focus", FG)],
              background=[("active", BG_BTN), ("!active", BG_BTN)])

        # ── Verbindung ────────────────────────────────────────────────────
        sep()
        sec(_t("sec_connection"))

        ports = [p.device for p in serial.tools.list_ports.comports()] if SERIAL_OK else []
        if ports and not self._port_var.get():
            self._port_var.set(ports[0])

        port_row = tk.Frame(body, bg=BG)
        port_row.pack(fill="x", padx=20, pady=(0, 8))
        RoundedBtn(port_row, _t("btn_search"), self._search_dongle_port,
                   w=72, h=28, r=7, p_bg=BG,
                   fill=BG_BTN, fg=FG_DIM, hover=BG_BTN_A, hover_fg=FG,
                   border_col=BORDER, font_spec=("Inter", 10)
                   ).pack(side="right")
        ttk.Combobox(port_row, textvariable=self._port_var,
                     values=ports, style="P.TCombobox").pack(side="left", fill="x",
                                                              expand=True, padx=(0, 8))

        is_connected = self._ser is not None
        self._settings_conn_btn = RoundedBtn(body,
                   "Disconnect" if is_connected else "Connect",
                   self._toggle_serial,
                   w=W, h=34, r=9, p_bg=BG,
                   fill=RED if is_connected else ACCENT,
                   fg="#ffffff",
                   hover="#c0392b" if is_connected else "#5591ff",
                   hover_fg="#ffffff",
                   font_spec=("Inter", 11, "bold")
                   )
        self._settings_conn_btn.pack(padx=20, pady=(0, 14))

        # ── Dongle-Board ──────────────────────────────────────────────────
        sep()
        sec(_t("sec_board"))
        board_frame = tk.Frame(body, bg=BG)
        board_frame.pack(fill="x", padx=20, pady=(0, 12))
        for val, label in (("nicenano", "Pro Micro nRF52840"),
                           ("holyiot",  "Holyiot nRF52840")):
            tk.Radiobutton(board_frame, text=label, variable=self._board_var, value=val,
                           bg=BG, fg=FG, selectcolor=BG_BTN,
                           activebackground=BG, activeforeground=ACCENT,
                           font=("Inter", 10),
                           command=self._on_board_change).pack(anchor="w", pady=2)

        # ── Versionen ─────────────────────────────────────────────────────
        sep()
        sec(_t("sec_versions"))
        ver_frame = tk.Frame(body, bg=BG)
        ver_frame.pack(fill="x", padx=20, pady=(0, 14))
        for label, var, color in [
            ("Server",  tk.StringVar(value=SERVER_VERSION), ACCENT),
            ("Dongle",  self._dongle_ver_var,               FG),
            ("Headpat", self._hp_ver_var,                   FG),
        ]:
            r = tk.Frame(ver_frame, bg=BG)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=label, bg=BG, fg=FG_DIM,
                     font=("Inter", 10)).pack(side="left")
            tk.Label(r, textvariable=var, bg=BG, fg=color,
                     font=("Inter", 10, "bold")).pack(side="right")

        # ── Sprache + Autostart ───────────────────────────────────────────
        sep()
        bot_row = tk.Frame(body, bg=BG)
        bot_row.pack(fill="x", padx=20, pady=(10, 14))

        lang_frame = tk.Frame(bot_row, bg=BG)
        lang_frame.pack(side="left")
        tk.Label(lang_frame, text=_t("sec_language").upper(), bg=BG, fg=FG_DIM,
                 font=("Inter", 8, "bold")).pack(anchor="w")
        lang_combo = ttk.Combobox(lang_frame, textvariable=self._lang_var,
                                  values=["de", "en"], width=7,
                                  style="P.TCombobox", state="readonly")
        lang_combo.pack(anchor="w", pady=(4, 0))

        def _on_lang_change(*_):
            global _LANG
            _LANG = self._lang_var.get()
            self._save_config()
            win.destroy()
            self.after(30, self._open_settings)
        self._lang_var.trace_add("write", _on_lang_change)

        as_frame = tk.Frame(bot_row, bg=BG)
        as_frame.pack(side="right")
        tk.Label(as_frame, text="AUTOSTART", bg=BG, fg=FG_DIM,
                 font=("Inter", 8, "bold")).pack(anchor="e")

        _as_state = [self._autostart_enabled()]
        TW, TH = 38, 22
        toggle_cvs = tk.Canvas(as_frame, width=TW, height=TH, bg=BG,
                               highlightthickness=0, cursor="hand2")
        toggle_cvs.pack(anchor="e", pady=(6, 0))

        def _draw_toggle(on):
            toggle_cvs.delete("all")
            col = ACCENT if on else BG_BTN
            r = TH // 2
            toggle_cvs.create_oval(0, 0, TH, TH, fill=col, outline="")
            toggle_cvs.create_oval(TW - TH, 0, TW, TH, fill=col, outline="")
            toggle_cvs.create_rectangle(r, 0, TW - r, TH, fill=col, outline="")
            tx = TW - TH + 2 if on else 2
            toggle_cvs.create_oval(tx, 2, tx + TH - 4, TH - 2,
                                   fill="#ffffff", outline="")
        _draw_toggle(_as_state[0])

        def _toggle_autostart(_=None):
            _as_state[0] = not _as_state[0]
            self._set_autostart(_as_state[0])
            _draw_toggle(_as_state[0])
        toggle_cvs.bind("<Button-1>", _toggle_autostart)

        # ── Positionierung ────────────────────────────────────────────────
        win.update_idletasks()
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width() + 8
        y = self.winfo_y()
        win.geometry(f"+{x}+{y}")
        win.deiconify()
        self.after(0, lambda: self._round_toplevel(win))

    # ── Restart ───────────────────────────────────────────────────────────────
    def _restart_app(self):
        if os.name == "nt":
            import ctypes
            if getattr(sys, "frozen", False):
                ctypes.windll.shell32.ShellExecuteW(None, "open", sys.executable, None, None, 1)
            else:
                import subprocess
                subprocess.Popen([sys.executable, os.path.abspath(__file__)])
        self.after(300, self._on_close)

    # ── Autostart ─────────────────────────────────────────────────────────────
    _AUTOSTART_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
    _AUTOSTART_NAME = "HeadpatServer"

    def _autostart_cmd(self):
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        return f'"{sys.executable}" "{os.path.abspath(__file__)}"'

    def _autostart_enabled(self):
        if os.name != "nt":
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._AUTOSTART_KEY) as k:
                winreg.QueryValueEx(k, self._AUTOSTART_NAME)
            return True
        except Exception:
            return False

    def _set_autostart(self, enable: bool):
        if os.name != "nt":
            return
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._AUTOSTART_KEY,
                                0, winreg.KEY_SET_VALUE) as k:
                if enable:
                    winreg.SetValueEx(k, self._AUTOSTART_NAME, 0,
                                      winreg.REG_SZ, self._autostart_cmd())
                else:
                    try:
                        winreg.DeleteValue(k, self._AUTOSTART_NAME)
                    except FileNotFoundError:
                        pass
        except Exception as e:
            self._log(f"[AUTOSTART] Fehler: {e}", "err")

    def _close_settings(self):
        self._settings_open = False
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.destroy()
        self._settings_win = None
        self._settings_conn_btn = None

    # ── Serial ────────────────────────────────────────────────────────────────
    def _refresh_ports(self):
        if not SERIAL_OK:
            return
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if ports and not self._port_var.get():
            self._port_var.set(ports[0])

    def _auto_find_dongle_port(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        for port in ports:
            try:
                with serial.Serial(port, BAUD, timeout=1) as s:
                    time.sleep(0.1)
                    s.reset_input_buffer()
                    s.write(b"info\n")
                    data = b""
                    deadline = time.time() + 1.2
                    while time.time() < deadline:
                        if s.in_waiting:
                            data += s.read(s.in_waiting)
                        if b"Headpat Dongle" in data:
                            return port
                        time.sleep(0.05)
            except Exception:
                pass
        return None

    def _search_dongle_port(self):
        with self._ser_lock:
            ser = self._ser
        if ser:
            self._log(f"Dongle bereits verbunden: {ser.port}", "info")
            self._port_var.set(ser.port)
            return
        self._log("Suche Headpat-Dongle…", "info")
        def _run():
            port = self._auto_find_dongle_port()
            if port:
                self._port_var.set(port)
                self._log(f"Dongle gefunden: {port}", "info")
            else:
                self._log("Kein Headpat-Dongle gefunden", "warn")
        threading.Thread(target=_run, daemon=True).start()

    def _toggle_serial(self):
        if self._ser:
            self._disconnect()
        else:
            self._connect()

    def _update_conn_btn(self):
        btn = self._settings_conn_btn
        if not btn or not btn.winfo_exists():
            return
        connected = self._ser is not None
        btn._text = "Disconnect" if connected else "Connect"
        btn.set_style(
            RED    if connected else ACCENT,
            "#ffffff",
            "#c0392b" if connected else "#5591ff",
            "#ffffff",
        )

    def _connect(self):
        port = self._port_var.get()
        if not SERIAL_OK:
            return
        if not port:
            self._log("Kein Port ausgewählt", "warn")
            return
        threading.Thread(target=self._connect_bg, args=(port,), daemon=True).start()

    def _connect_bg(self, port):
        try:
            ser = serial.Serial(port, BAUD, timeout=1)
            with self._ser_lock:
                self._ser = ser
            self._log(f"Verbunden: {port}", "info")
            threading.Thread(target=self._serial_loop, daemon=True).start()
            self.after(0, self._save_config)
            self.after(0, self._update_conn_btn)
        except Exception as e:
            self._log(f"Verbindungsfehler: {e}", "err")

    def _disconnect(self):
        with self._ser_lock:
            ser, self._ser = self._ser, None
        if ser:
            try: ser.write(b"m:00\n")
            except: pass
            try: ser.close()
            except: pass
        self._ble_connected = False
        self._set_dot(self._hp_dot, RED)
        self._bat_text = "🔋 ?%"; self._bat_fg = FG_DIM
        self._bat_lbl.config(text=self._bat_text, fg=self._bat_fg)
        # Versionen zurücksetzen, damit Update-Check nach Reconnect wieder korrekt arbeitet
        self._hp_version     = "?"
        self._dongle_version = "?"
        self._hp_ver_var.set("?")
        self._dongle_ver_var.set("?")
        self._updates.pop("headpat", None)
        self._updates.pop("dongle",  None)
        self._log("Verbindung getrennt", "warn")
        self._save_config()
        self.after(0, self._update_conn_btn)

    def _serial_loop(self):
        last_info = 0.0
        last_bat  = 0.0
        with self._ser_lock:
            ser = self._ser
        if ser:
            try: ser.write(b"info\n")
            except: pass

        while True:
            with self._ser_lock:
                ser = self._ser
            if ser is None:
                break
            try:
                now = time.time()
                if now - last_info >= INFO_INTERVAL:
                    ser.write(b"info\n")
                    last_info = now
                if self._ble_connected and now - last_bat >= BAT_INTERVAL:
                    ser.write(b"reqbat\n")
                    last_bat = now

                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                self._log(line, "serial")

                m = re.search(r'\[BAT\]\s*(\d+)', line)
                if m:
                    self._q.put(("bat", int(m.group(1))))
                    continue

                m = re.search(r'\[VER\]\s*(Headpat\s+v[\d.]+)', line)
                if m:
                    self._q.put(("hp_ver", m.group(1)))
                    continue

                m = re.search(r'Headpat\s+Dongle\s+(v[\d.]+)', line)
                if m:
                    self._q.put(("dongle_ver", m.group(1)))
                    continue

                if re.search(r'\[BLE\]\s*Connected:', line):
                    self._q.put(("hp_ble", True))
                    try:
                        ser.write(b"reqbat\n")
                        ser.write(b"reqver\n")
                    except: pass
                    last_bat = now
                    continue

                if re.search(r'\[BLE\]\s*Disconnected', line):
                    self._q.put(("hp_ble", False))
                    continue

                if line.startswith("Connected:"):
                    val_str = line.split(":", 1)[1].strip()
                    if "/" in val_str:
                        up = val_str.split("/")[0].strip() != "0"
                    else:
                        up = val_str.upper() == "YES"
                    self._q.put(("hp_ble", up))
                    if up and not self._ble_connected:
                        try:
                            ser.write(b"reqbat\n")
                            ser.write(b"reqver\n")
                        except: pass
                        last_bat = now

            except Exception:
                self._q.put(("serial_lost", None))
                break

    def _send_motor(self, left_n: int, right_n: int):
        left_n  = max(0, min(15, left_n))
        right_n = max(0, min(15, right_n))
        with self._ser_lock:
            ser = self._ser
        if ser:
            try: ser.write(f"m:{(left_n << 4 | right_n):02X}\n".encode())
            except: pass

    def _pat_left(self):
        n = int(15 * self._intensity)
        self._send_motor(n, 0)
        self.after(400, lambda: self._send_motor(0, 0))

    def _pat_right(self):
        n = int(15 * self._intensity)
        self._send_motor(0, n)
        self.after(400, lambda: self._send_motor(0, 0))

    # ── OSC ──────────────────────────────────────────────────────────────────
    def _start_osc(self):
        if not OSC_OK:
            self._log("python-osc nicht installiert — OSC deaktiviert", "err")
            return
        self._log(f"OSC lauscht auf {OSC_HOST}:{OSC_RX_PORT}", "info")
        threading.Thread(target=self._osc_loop, daemon=True).start()

    def _osc_loop(self):
        try:
            d = dispatcher.Dispatcher()
            d.set_default_handler(self._osc_recv)
            osc_server.ThreadingOSCUDPServer((OSC_HOST, OSC_RX_PORT), d).serve_forever()
        except Exception as e:
            self._log(f"OSC-Fehler: {e}", "err")

    def _osc_recv(self, address: str, *args):
        val_str = f"{float(args[0]):.3f}" if args else "?"

        # Determine filter status
        is_avatar = address.startswith("/avatar/parameters/")
        if is_avatar:
            pname = address.split("/")[-1].lower()
            is_hp = bool(_MOTOR_RE.search(pname))
            status = "PASS" if is_hp else "skip"
        else:
            status = "----"

        # Log to console
        if status == "PASS":
            self._log(f"[OSC] {address} = {val_str}", "PASS")
        elif self._osc_verbose:
            self._log(f"[OSC] {status} {address} = {val_str}",
                      "skip" if status == "skip" else "osc")

        if not is_avatar:
            return

        # Any avatar parameter proves VRChat OSC is alive
        self._last_osc = time.time()
        if not self._vrc_connected:
            self._vrc_connected = True
            self._q.put(("vrc", True))

        # only direct parameters: /avatar/parameters/<name> — not nested paths like /avatar/parameters/VF158_Toggles/Headpat
        parts = address.split("/")
        if len(parts) != 4:
            return

        param = parts[3].lower()
        if not _MOTOR_RE.search(param):
            return

        with self._ser_lock:
            if self._ser is None:
                return

        val = float(args[0]) if args else 0.0
        stop_at = 0.5 if self._vib_mode == 1 else 0.1
        if val < stop_at:
            self._send_motor(0, 0)
            return
        if self._vib_mode == 1:
            nibble = max(1, int(15 * self._intensity))
        else:
            nibble = max(0, min(15, int(val * 15 * self._intensity)))
        self._last_motor_nz = time.time()
        if   re.search(r'\bleft\b',  param): self._send_motor(nibble, 0)
        elif re.search(r'\bright\b', param): self._send_motor(0, nibble)
        else:                                self._send_motor(nibble, nibble)

    # ── Tick ─────────────────────────────────────────────────────────────────
    def _tick(self):
        try:
            while True:
                tag, val = self._q.get_nowait()
                if tag == "bat":
                    pct = int(val)
                    col = GREEN if pct >= 50 else YELLOW if pct >= 20 else RED
                    self._bat_text = f"🔋 {pct}%"; self._bat_fg = col
                    self._bat_lbl.config(text=self._bat_text, fg=self._bat_fg)
                elif tag == "hp_ble":
                    self._ble_connected = val
                    self._set_dot(self._hp_dot, GREEN if val else RED)
                    if not val:
                        self._bat_text = "🔋 ?%"; self._bat_fg = FG_DIM
                        self._bat_lbl.config(text=self._bat_text, fg=self._bat_fg)
                elif tag == "vrc":
                    self._vrc_connected = val
                    self._set_dot(self._vrc_dot, GREEN if val else RED)
                elif tag == "hp_ver":
                    self._hp_version = val
                    self._hp_ver_var.set(val)
                    self._recheck_firmware_updates()
                elif tag == "dongle_ver":
                    self._dongle_version = val
                    self._dongle_ver_var.set(val)
                    self._recheck_firmware_updates()
                elif tag == "serial_lost":
                    self._disconnect()
                elif tag == "update_found":
                    key, ver = val
                    names = {"headpat": "Headpat", "dongle": "Dongle", "server": "Server"}
                    self._log(f"Update verfügbar: {names.get(key, key)} {ver}", "warn")
                    self._set_badge_active(True)
                elif tag == "nrf52_drive":
                    self._on_nrf52_drive(val)
                elif tag == "log":
                    if (self._console_win and self._console_win.winfo_exists()
                            and self._console_text):
                        ts, ltag, text = val
                        self._console_text.config(state="normal")
                        self._console_text.insert("end", f"{ts}  {text}\n", ltag)
                        n = int(self._console_text.index("end-1c").split(".")[0])
                        if n > 500:
                            self._console_text.delete("1.0", f"{n - 500}.0")
                        self._console_text.see("end")
                        self._console_text.config(state="disabled")
        except queue.Empty:
            pass

        now = time.time()
        if self._vrc_connected and now - self._last_osc > VRC_TIMEOUT:
            self._vrc_connected = False
            self._set_dot(self._vrc_dot, RED)
            self._send_motor(0, 0)  # VRC weg → Motoren sofort stoppen

        # Watchdog: kein Motor-Update seit 150ms → stoppen
        if self._last_motor_nz and now - self._last_motor_nz > 0.15:
            self._last_motor_nz = 0.0
            self._send_motor(0, 0)

        self.after(100, self._tick)


def _crash_write(header, text):
    try:
        _log_dir  = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HeadpatServer")
        os.makedirs(_log_dir, exist_ok=True)
        with open(os.path.join(_log_dir, "crash.log"), "a", encoding="utf-8") as _f:
            _f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {header} ===\n")
            _f.write(text)
    except Exception:
        pass

if __name__ == "__main__":
    import traceback as _tb2
    try:
        app = App()

        def _tk_exc(exc_type, exc_val, exc_tb):
            _crash_write("(tk callback)", "".join(_tb2.format_exception(exc_type, exc_val, exc_tb)))

        app.report_callback_exception = _tk_exc
        app.mainloop()
    except Exception:
        _crash_write("(startup)", _tb2.format_exc())
