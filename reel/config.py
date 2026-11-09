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


def local() -> dict:
    """Impostazioni di questo PC (config/local.yaml, creato dall'installer, non versionato)."""
    path = CONFIG_DIR / "local.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def desktop() -> Path:
    import os
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for cand in (home / "OneDrive" / "Desktop", home / "OneDrive" / "Scrivania", home / "Desktop", home / "Scrivania"):
        if cand.is_dir():
            return cand
    return home


def studio_dir() -> Path:
    import os
    env = os.environ.get("REEL_STUDIO_DIR")  # usato dai test per non toccare il Desktop
    return Path(env or local().get("studio_dir") or desktop() / "Reel Studio")


def inbox() -> Path:
    import os
    if os.environ.get("REEL_STUDIO_DIR"):
        return studio_dir() / "1 - Video da montare"
    return Path(local().get("inbox") or studio_dir() / "1 - Video da montare")


def outbox() -> Path:
    import os
    if os.environ.get("REEL_STUDIO_DIR"):
        return studio_dir() / "2 - Video pronti"
    return Path(local().get("outbox") or studio_dir() / "2 - Video pronti")


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
