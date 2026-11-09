"""Percorsi e caricamento configurazione."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
ASSETS = ROOT / "assets"
PROJECTS = ROOT / "projects"
FONTS = ASSETS / "fonts"


def load(name: str) -> dict:
    with open(CONFIG_DIR / f"{name}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def export_cfg() -> dict:
    return load("export")


def caption_presets() -> dict:
    return load("caption_presets")


def brand() -> dict:
    return load("brand")


def glossary() -> list[str]:
    path = CONFIG_DIR / "glossario.txt"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def project_dir(name: str) -> Path:
    p = Path(name)
    if p.is_dir() and (p / "edl.json").exists() or (p.is_dir() and (p / "raw").exists()):
        return p.resolve()
    return (PROJECTS / name).resolve()
