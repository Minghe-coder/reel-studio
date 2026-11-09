"""EDL (Edit Decision List): il montaggio descritto come dati in projects/<nome>/edl.json.

Tempi: i `segments` sono in secondi del file SORGENTE. Tutti gli altri eventi
(testi, pop-up, sfx, transizioni) usano un "anchor" che viene risolto sulla
timeline di USCITA al momento del render, così sopravvivono ai ri-tagli:
  - numero            -> secondi sulla timeline finale (negativo = dalla fine, es. -3)
  - {"word": "gratis", "n": 1}     -> inizio della n-esima volta che dici quella parola/frase
  - {"word": "...", "n": 1, "edge": "end"} -> fine della parola/frase
  - {"src": 0, "t": 12.3}          -> istante del file sorgente 0
  - {"segment": 3}                 -> inizio del segmento 3 (0-based)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

DEFAULT_EDL: dict = {
    "version": 1,
    "sources": [],
    "segments": [],
    "captions": {
        "enabled": True,
        "preset": "bold",
        "highlight_words": [],
        "replacements": {},
        "emoji": {},
    },
    "texts": [],
    "popups": [],
    "transitions": [],
    "sfx": [],
    "music": {"file": None, "volume": 0.15, "duck": True, "fade_in": 0.5, "fade_out": 1.5},
    "audio": {"denoise": True, "voice_eq": True, "compress": True},
    "progress_bar": {"enabled": False, "color": None, "height": 12},
    "color": {"lut": None, "saturation": 1.0, "contrast": 1.0, "brightness": 0.0},
}


def new_edl() -> dict:
    return copy.deepcopy(DEFAULT_EDL)


def load(project: Path) -> dict:
    path = project / "edl.json"
    if not path.exists():
        return new_edl()
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = new_edl()
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k].update(v)
        else:
            merged[k] = v
    return merged


def save(project: Path, edl: dict, backup: bool = True) -> None:
    path = project / "edl.json"
    if backup and path.exists():
        hist = project / ".history"
        hist.mkdir(exist_ok=True)
        n = len(list(hist.glob("edl-*.json"))) + 1
        (hist / f"edl-{n:04d}.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(json.dumps(edl, indent=2, ensure_ascii=False), encoding="utf-8")


def undo(project: Path) -> bool:
    hist = project / ".history"
    snaps = sorted(hist.glob("edl-*.json")) if hist.exists() else []
    if not snaps:
        return False
    last = snaps[-1]
    (project / "edl.json").write_text(last.read_text(encoding="utf-8"), encoding="utf-8")
    last.unlink()
    return True


def validate(edl: dict) -> list[str]:
    """Controlli di coerenza; restituisce una lista di problemi (vuota = ok)."""
    errs = []
    ids = {s["id"] for s in edl["sources"]}
    for i, seg in enumerate(edl["segments"]):
        if seg["src"] not in ids:
            errs.append(f"segmento {i}: sorgente {seg['src']} inesistente")
        if seg["out"] <= seg["in"]:
            errs.append(f"segmento {i}: out <= in")
        src = next((s for s in edl["sources"] if s["id"] == seg["src"]), None)
        if src and seg["out"] > src["duration"] + 0.05:
            errs.append(f"segmento {i}: out oltre la durata del sorgente")
    return errs
