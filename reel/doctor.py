"""Verifica dell'installazione."""
from __future__ import annotations

import importlib.util
import platform
import shutil
import sys

from . import config, ff


def run() -> bool:
    ok = True

    def line(good: bool, msg: str, fix: str = ""):
        nonlocal ok
        ok &= good
        print(("  OK   " if good else "  !!   ") + msg + ("" if good or not fix else f"\n         -> {fix}"))

    print(f"Sistema: {platform.system()} {platform.release()} · Python {sys.version.split()[0]}")
    line(sys.version_info >= (3, 10), "Python >= 3.10", "installa Python 3.12: winget install Python.Python.3.12")
    has_ff = shutil.which("ffmpeg") and shutil.which("ffprobe")
    line(bool(has_ff), "FFmpeg e ffprobe nel PATH", "winget install Gyan.FFmpeg  (poi riapri il terminale)")
    if has_ff:
        v = ff.version()
        line(v >= (6, 0), f"FFmpeg versione {v[0]}.{v[1]} (serve >= 6)", "aggiorna: winget upgrade Gyan.FFmpeg")
        for flt in ("subtitles", "sidechaincompress", "loudnorm", "afftdn", "drawbox"):
            line(ff.has_filter(flt), f"filtro ffmpeg '{flt}'", "usa la build 'full' di gyan.dev")
    line(importlib.util.find_spec("yaml") is not None, "PyYAML", "pip install -r requirements.txt")
    line(importlib.util.find_spec("faster_whisper") is not None, "faster-whisper (trascrizione)", "pip install -r requirements.txt")
    fonts = list(config.FONTS.glob("*.ttf")) + list(config.FONTS.glob("*.otf"))
    line(bool(fonts), f"font in assets/fonts ({len(fonts)})", "aggiungi i .ttf in assets/fonts")
    sfx = list((config.ASSETS / "sfx").rglob("*.wav")) + list((config.ASSETS / "sfx").rglob("*.mp3"))
    line(bool(sfx), f"effetti sonori in assets/sfx ({len(sfx)})", "python -m reel sfx-base")
    music = [p for p in (config.ASSETS / "music").rglob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a"}]
    print(f"  ..   musica in assets/music: {len(music)} file" + ("" if music else " (aggiungine qualcuna, vedi MATERIALI.md)"))
    node = shutil.which("node")
    print(f"  ..   Node.js (solo per la fase 2 Remotion): {'presente' if node else 'assente (facoltativo)'}")
    print("\nTutto pronto!" if ok else "\nSistema i punti con '!!' e rilancia: python -m reel doctor")
    return ok
