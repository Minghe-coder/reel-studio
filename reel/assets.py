"""Libreria asset: catalogo musica/SFX, SFX di base generati, emoji PNG."""
from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

from . import config, ff

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

# SFX sintetizzati con ffmpeg: royalty-free al 100% perché li generi tu.
BASIC_SFX = {
    "pop/pop_1.wav": "sine=f=900:d=0.09,afade=t=out:st=0.0:d=0.09,asetrate=48000*1.3,aresample=48000,volume=1.6",
    "pop/pop_2.wav": "sine=f=600:d=0.07,vibrato=f=40:d=0.6,afade=t=out:st=0:d=0.07,volume=1.6",
    "click/click_1.wav": "anoisesrc=d=0.02:c=white:a=0.8,highpass=f=2500,afade=t=out:st=0:d=0.02",
    "ding/ding_1.wav": "sine=f=1760:d=0.9,afade=t=out:st=0.02:d=0.88,volume=0.7",
    "boom/boom_1.wav": "sine=f=55:d=0.9,afade=t=out:st=0.05:d=0.85,volume=2.5,alimiter=limit=0.95",
    "whoosh/whoosh_1.wav": "anoisesrc=d=0.45:c=pink:a=0.9,bandpass=f=1200:w=1500,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2,volume=1.5",
    "whoosh/whoosh_2.wav": "anoisesrc=d=0.3:c=white:a=0.6,highpass=f=800,lowpass=f=6000,afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.18",
    "glitch/glitch_1.wav": "anoisesrc=d=0.25:c=white:a=0.5,acrusher=bits=4:samples=20,afade=t=out:st=0.15:d=0.1",
    "typing/typing_1.wav": "anoisesrc=d=1.2:c=white:a=0.6,highpass=f=3000,apulsator=hz=9:amount=1,afade=t=out:st=1.0:d=0.2,volume=0.7",
}


def make_basic_sfx(overwrite: bool = False) -> list[str]:
    made = []
    for rel, expr in BASIC_SFX.items():
        dst = config.ASSETS / "sfx" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not overwrite:
            continue
        ff.run(["ffmpeg", "-y", "-hide_banner", "-f", "lavfi", "-i", expr, "-ar", "48000", "-ac", "2", str(dst)])
        made.append(rel)
    return made


def catalog() -> dict[str, int]:
    """Aggiorna assets/music/music_catalog.csv e assets/sfx/sfx_catalog.csv mantenendo le note scritte a mano."""
    counts = {}
    for kind in ("music", "sfx"):
        base = config.ASSETS / kind
        path = base / f"{kind}_catalog.csv"
        old = {}
        if path.exists():
            with open(path, encoding="utf-8", newline="") as fh:
                old = {r["file"]: r for r in csv.DictReader(fh)}
        rows = []
        for f in sorted(base.rglob("*")):
            if f.suffix.lower() not in AUDIO_EXT:
                continue
            rel = f.relative_to(config.ROOT).as_posix()
            try:
                dur = round(ff.probe(f)["duration"], 2)
            except ff.FFmpegError:
                dur = ""
            prev = old.get(rel, {})
            rows.append({"file": rel, "categoria": f.parent.name, "durata_s": dur,
                         "bpm": prev.get("bpm", ""), "energia_1_5": prev.get("energia_1_5", ""),
                         "licenza": prev.get("licenza", "generato" if kind == "sfx" and f.name.split("_")[0] in {
                             "pop", "click", "ding", "boom", "whoosh", "glitch", "typing"} else ""),
                         "fonte": prev.get("fonte", ""), "note": prev.get("note", "")})
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["file", "categoria", "durata_s", "bpm", "energia_1_5", "licenza", "fonte", "note"])
            w.writeheader()
            w.writerows(rows)
        counts[kind] = len(rows)
    return counts


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read()


def emoji_png(char: str, size: int = 512) -> Path:
    """Scarica (una volta) l'emoji come PNG grande da Twemoji (licenza CC-BY 4.0).
    Prova lo SVG (nitido a ogni dimensione, se FFmpeg ha librsvg), altrimenti il PNG 72px ingrandito."""
    cps = [f"{ord(c):x}" for c in char if ord(c) != 0xFE0F]
    code = "-".join(cps)
    dst = config.ASSETS / "overlays" / "emoji" / f"{code}.png"
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    base = "https://raw.githubusercontent.com/jdecked/twemoji/main/assets"
    tmp = dst.with_suffix(".src")
    try:
        try:
            tmp.write_bytes(_download(f"{base}/svg/{code}.svg"))
            ff.run(["ffmpeg", "-y", "-hide_banner", "-f", "svg_pipe", "-i", str(tmp),
                    "-vf", f"scale={size}:{size}:flags=lanczos", "-frames:v", "1", str(dst)])
        except (ff.FFmpegError, OSError):
            tmp.write_bytes(_download(f"{base}/72x72/{code}.png"))
            ff.run(["ffmpeg", "-y", "-hide_banner", "-i", str(tmp), "-vf", f"scale={size}:{size}:flags=lanczos",
                    "-frames:v", "1", str(dst)])
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Impossibile scaricare l'emoji {char}: {exc}. "
                         f"Salva un PNG a mano in {dst.parent} e usa --image.") from exc
    finally:
        tmp.unlink(missing_ok=True)
    return dst
