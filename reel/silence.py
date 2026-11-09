"""Rilevamento silenzi con ffmpeg silencedetect, con soglia adattiva al livello del microfono."""
from __future__ import annotations

import re
from pathlib import Path

from . import ff


def speech_level(path: Path | str) -> float:
    """Stima il livello della voce (dB) come il 'max' di volumedetect meno un margine."""
    proc = ff.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                   "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", proc.stderr)
    return float(mean.group(1)) if mean else -25.0


def auto_threshold(path: Path | str) -> float:
    """Soglia silenzio = volume medio - 16 dB, limitata tra -50 e -28 dB."""
    return max(-50.0, min(-28.0, speech_level(path) - 16.0))


def detect(path: Path | str, threshold_db: float | None = None, min_dur: float = 0.4) -> list[tuple[float, float]]:
    if threshold_db is None:
        threshold_db = auto_threshold(path)
    proc = ff.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                   "-af", f"silencedetect=noise={threshold_db:.1f}dB:d={min_dur}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", proc.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", proc.stderr)]
    dur = ff.probe(path)["duration"]
    res = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else dur
        res.append((max(0.0, s), min(dur, e)))
    return res
