"""Controllo qualità dell'export finale."""
from __future__ import annotations

from pathlib import Path

from . import config, ff


def check(project: Path, video: Path) -> dict:
    exp = config.export_cfg()
    info = ff.probe(video)
    loud = ff.measure_loudness(video)
    problems = []
    if (info.get("width"), info.get("height")) != (exp["width"], exp["height"]):
        problems.append(f"risoluzione {info.get('width')}x{info.get('height')} (attesa {exp['width']}x{exp['height']})")
    if abs((info.get("fps") or 0) - exp["fps"]) > 0.5:
        problems.append(f"fps {info.get('fps')} (attesi {exp['fps']})")
    if info.get("vcodec") != "h264":
        problems.append(f"codec video {info.get('vcodec')} (atteso h264)")
    if info.get("acodec") != "aac":
        problems.append(f"codec audio {info.get('acodec')} (atteso aac)")
    if loud["integrated"] is not None and abs(loud["integrated"] - exp["loudness_lufs"]) > 1.5:
        problems.append(f"loudness {loud['integrated']} LUFS (target {exp['loudness_lufs']})")
    if loud["true_peak"] is not None and loud["true_peak"] > exp["true_peak_db"] + 0.5:
        problems.append(f"true peak {loud['true_peak']} dBTP troppo alto")
    if info["duration"] > 90:
        problems.append(f"durata {info['duration']:.0f}s: per Reels/TikTok stai sotto 90 s (ideale 20–45 s)")
    size_mb = video.stat().st_size / 1e6
    # fotogrammi di controllo con le zone sicure disegnate
    qc_dir = project / "out" / "qc"
    qc_dir.mkdir(parents=True, exist_ok=True)
    sz = exp["safe_zone"]
    W, H = exp["width"], exp["height"]
    overlay = (f"drawbox=x=0:y=0:w={W}:h={sz['top']}:color=red@0.25:t=fill,"
               f"drawbox=x=0:y={H - sz['bottom']}:w={W}:h={sz['bottom']}:color=red@0.25:t=fill,"
               f"drawbox=x={W - sz['right']}:y=0:w={sz['right']}:h={H}:color=red@0.25:t=fill")
    shots = []
    for k, frac in enumerate((0.1, 0.35, 0.6, 0.9)):
        t = info["duration"] * frac
        out = qc_dir / f"frame_{k + 1}.jpg"
        ff.run(["ffmpeg", "-y", "-hide_banner", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                "-vf", f"{overlay},scale=540:-1", "-q:v", "3", str(out)])
        shots.append(str(out.relative_to(project)))
    return {"file": str(video.name), "duration": round(info["duration"], 2), "resolution": f"{info.get('width')}x{info.get('height')}",
            "fps": info.get("fps"), "size_mb": round(size_mb, 1), "loudness": loud, "problems": problems, "frames": shots}
