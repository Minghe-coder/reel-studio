"""Wrapper minimi attorno a ffmpeg/ffprobe."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise FFmpegError(
            f"'{binary}' non trovato. Installa FFmpeg (vedi SETUP-WINDOWS.md) e riapri il terminale."
        )
    return path


def run(args: list[str], cwd: Path | str | None = None, quiet: bool = True) -> subprocess.CompletedProcess:
    """Esegue ffmpeg/ffprobe; solleva FFmpegError con la coda dello stderr se fallisce."""
    cmd = [require(args[0]), *args[1:]]
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-25:])
        raise FFmpegError(f"Comando fallito: {' '.join(cmd[:6])} ...\n{tail}")
    if not quiet:
        print(proc.stderr)
    return proc


def probe(path: Path | str) -> dict:
    """Restituisce info essenziali su un file video/audio."""
    proc = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    data = json.loads(proc.stdout)
    info: dict = {
        "path": str(path),
        "duration": float(data.get("format", {}).get("duration", 0) or 0),
        "has_video": False,
        "has_audio": False,
    }
    for st in data.get("streams", []):
        if st.get("codec_type") == "video" and not info["has_video"]:
            if st.get("disposition", {}).get("attached_pic"):
                continue
            info["has_video"] = True
            w, h = int(st.get("width", 0)), int(st.get("height", 0))
            rot = 0
            for sd in st.get("side_data_list", []) or []:
                if "rotation" in sd:
                    rot = int(sd["rotation"])
            if "rotate" in (st.get("tags") or {}):
                rot = int(st["tags"]["rotate"])
            if abs(rot) % 180 == 90:
                w, h = h, w
            info.update(
                width=w,
                height=h,
                rotation=rot,
                vcodec=st.get("codec_name"),
                fps=_fps(st.get("avg_frame_rate") or st.get("r_frame_rate")),
                r_fps=_fps(st.get("r_frame_rate")),
                pix_fmt=st.get("pix_fmt"),
            )
        elif st.get("codec_type") == "audio" and not info["has_audio"]:
            info["has_audio"] = True
            info.update(acodec=st.get("codec_name"), sample_rate=int(st.get("sample_rate", 0) or 0),
                        channels=st.get("channels"))
    if info["has_video"]:
        info["vfr"] = abs(info.get("fps", 0) - info.get("r_fps", 0)) > 0.5
    return info


def _fps(rate: str | None) -> float:
    if not rate or rate in ("0/0",):
        return 0.0
    if "/" in rate:
        n, d = rate.split("/")
        return round(float(n) / float(d), 3) if float(d) else 0.0
    return float(rate)


def measure_loudness(path: Path | str) -> dict:
    """Misura loudness integrata (LUFS) e true peak con il filtro ebur128."""
    proc = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                "-af", "ebur128=peak=true", "-f", "null", "-"])
    text = proc.stderr
    summary = text[text.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summary)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", summary)
    def f(m):
        if not m:
            return None
        return float("-inf") if m.group(1) == "-inf" else float(m.group(1))
    return {"integrated": f(i), "true_peak": f(tp), "lra": f(lra)}


def has_filter(name: str) -> bool:
    proc = run(["ffmpeg", "-hide_banner", "-filters"])
    return re.search(rf"^\s*\S+\s+{re.escape(name)}\s", proc.stdout, re.M) is not None


def version() -> tuple[int, int]:
    """Versione di ffmpeg (major, minor); (99, 0) per build git senza numero."""
    proc = run(["ffmpeg", "-hide_banner", "-version"])
    m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", proc.stdout)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 0)
