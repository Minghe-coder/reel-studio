"""Creazione progetto e import dei file grezzi."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import config, edl as E, ff

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".mts"}

SCALETTA = """# Scaletta: {name}

**Obiettivo del video:** (cosa deve pensare/fare chi guarda alla fine?)
**Durata target:** 30 s   ·   **Piattaforma:** IG Reels + TikTok

| Tempo | Blocco | Cosa dico | A schermo / effetti |
|---|---|---|---|
| 0–3 s | HOOK | | testo hook grande + zoom + SFX boom |
| 3–8 s | PROMESSA | "In 30 secondi ti mostro…" | sottotitoli + pop-up icona |
| 8–16 s | PUNTO 1 | | numero "1" + zoom punch-in |
| 16–24 s | PUNTO 2 | | numero "2" + screenshot/B-roll |
| 24–32 s | PUNTO 3 | | numero "3" + pop-up |
| ultimi 3–5 s | CTA / LOOP | "Salva il video / Seguimi per…" | testo CTA + SFX ding |

**Caption del post:**
**Hashtag (3–5):**
**Musica (mood):**
"""


def create(name: str) -> Path:
    p = config.PROJECTS / name
    (p / "raw").mkdir(parents=True, exist_ok=True)
    (p / "broll").mkdir(exist_ok=True)
    (p / "out").mkdir(exist_ok=True)
    if not (p / "scaletta.md").exists():
        (p / "scaletta.md").write_text(SCALETTA.format(name=name), encoding="utf-8")
    if not (p / "edl.json").exists():
        E.save(p, E.new_edl(), backup=False)
    return p


# HDR (iPhone "Dolby Vision"/HLG) -> SDR Rec.709: senza questo i colori escono slavati
HDR_TO_SDR = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
              "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def normalize(src: Path, dst: Path, fps: int = 30, hdr: bool = False) -> None:
    """Rende il file 'montabile': frame rate costante, rotazione applicata, HDR convertito, audio 48k.
    Usa CRF 16 (qualità quasi identica) per non perdere dettaglio."""
    vf = f"fps={fps},setsar=1"
    if hdr and ff.has_filter("zscale"):
        vf = HDR_TO_SDR + "," + vf
    ff.run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-colorspace", "bt709",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-movflags", "+faststart", str(dst)])


def ingest(project: Path, files: list[str] | None = None, force_normalize: bool = False) -> list[dict]:
    """Registra i file di raw/ come sorgenti. Se sono VFR (tipico dei telefoni) o HDR/HEVC 10 bit,
    crea una copia normalizzata in work/ e usa quella."""
    exp = config.export_cfg()
    raw = project / "raw"
    paths = [Path(f) for f in files] if files else sorted(x for x in raw.iterdir() if x.suffix.lower() in VIDEO_EXT)
    if not paths:
        raise SystemExit(f"Nessun video in {raw}. Copia lì i tuoi file e riprova.")
    work = project / "work"
    work.mkdir(exist_ok=True)
    edl = E.load(project)
    sources = []
    for i, path in enumerate(paths):
        if not path.is_absolute():
            path = (project / path) if (project / path).exists() else raw / path.name
        if path.parent != raw and not path.is_relative_to(project):
            shutil.copy2(path, raw / path.name)
            path = raw / path.name
        info = ff.probe(path)
        if not info["has_video"]:
            print(f"  salto {path.name}: nessuna traccia video")
            continue
        needs = force_normalize or info.get("vfr") or info.get("hdr") or (info.get("pix_fmt") or "").endswith("10le") \
            or abs(info.get("fps", 30) - exp["fps"]) > 0.5
        rel = path.relative_to(project).as_posix()
        if needs:
            dst = work / (path.stem + "_norm.mp4")
            if not dst.exists():
                print(f"  preparo {path.name} ({'HDR iPhone -> colori standard, ' if info.get('hdr') else ''}frame rate costante)...")
                normalize(path, dst, exp["fps"], bool(info.get("hdr")))
            info = ff.probe(dst)
            rel = dst.relative_to(project).as_posix()
        orient = "verticale" if info["height"] > info["width"] else "orizzontale" if info["width"] > info["height"] else "quadrato"
        sources.append({"id": len(sources), "path": rel, "original": path.name, "duration": round(info["duration"], 3),
                        "width": info["width"], "height": info["height"], "fps": info.get("fps"),
                        "has_audio": info["has_audio"], "orientation": orient})
        print(f"  [{len(sources) - 1}] {path.name}: {info['width']}x{info['height']} {info.get('fps')}fps "
              f"{info['duration']:.1f}s {orient}{'' if info['has_audio'] else ' (SENZA AUDIO)'}")
    edl["sources"] = sources
    edl["segments"] = [{"src": s["id"], "in": 0.0, "out": s["duration"], "zoom": 1.0} for s in sources]
    E.save(project, edl)
    return sources


def take_from_inbox(project: Path) -> list[Path]:
    """Sposta i video dalla cartella del Desktop '1 - Video da montare' in raw/ del progetto."""
    box = config.inbox()
    files = sorted(x for x in box.iterdir() if x.is_file() and x.suffix.lower() in VIDEO_EXT) if box.exists() else []
    moved = []
    for f in files:
        dst = project / "raw" / f.name
        shutil.move(str(f), dst)
        moved.append(dst)
    return moved


def deliver(project: Path, video: Path) -> Path:
    """Copia il video finito in '2 - Video pronti' sul Desktop con un nome leggibile."""
    box = config.outbox()
    box.mkdir(parents=True, exist_ok=True)
    stem = project.name if video.name == "final.mp4" else f"{project.name}_{video.stem}"
    dst = box / f"{stem}.mp4"
    shutil.copy2(video, dst)
    return dst
