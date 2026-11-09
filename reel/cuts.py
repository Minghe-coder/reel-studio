"""Taglio grezzo automatico: silenzi + intercalari, con margini di respiro."""
from __future__ import annotations

from . import timeline as tl

LEVELS = {
    #             silenzio minimo da tagliare, margine prima/dopo il parlato
    "leggero":    {"min_silence": 0.70, "pad": 0.15},
    "normale":    {"min_silence": 0.40, "pad": 0.10},
    "aggressivo": {"min_silence": 0.25, "pad": 0.06},
}

FILLERS_IT = {"ehm", "eh", "ehh", "ehmm", "uhm", "uh", "mm", "mmm", "hmm", "ah", "ahm", "boh"}


def speech_intervals(duration: float, silences: list[tuple[float, float]], min_silence: float,
                     pad: float) -> list[tuple[float, float]]:
    """Complemento dei silenzi (solo quelli >= min_silence), allargato di `pad`."""
    sil = [(a, b) for a, b in silences if b - a >= min_silence]
    keep, t = [], 0.0
    for a, b in sil:
        if a > t:
            keep.append((t, a))
        t = max(t, b)
    if t < duration:
        keep.append((t, duration))
    padded = [(max(0.0, a - pad), min(duration, b + pad)) for a, b in keep]
    merged: list[tuple[float, float]] = []
    for a, b in padded:
        if merged and a <= merged[-1][1] + 0.05:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if b - a >= 0.15]


def autocut(sources: list[dict], silences: dict[int, list[tuple[float, float]]], words: list[dict],
            level: str = "normale", remove_fillers: bool = True, extra_fillers: set[str] | None = None) -> tuple[list[dict], dict]:
    cfg = LEVELS[level]
    segments: list[dict] = []
    for s in sources:
        for a, b in speech_intervals(s["duration"], silences.get(s["id"], []), cfg["min_silence"], cfg["pad"]):
            segments.append({"src": s["id"], "in": round(a, 3), "out": round(b, 3), "zoom": 1.0})
    removed_fillers = []
    if remove_fillers and words:
        fill = FILLERS_IT | (extra_fillers or set())
        for w in words:
            if tl.norm(w["w"]) in fill:
                segments = tl.remove_src_range(segments, w["src"], w["s"] - 0.02, w["e"] + 0.02)
                removed_fillers.append(w)
    segments = [s for s in segments if s["out"] - s["in"] >= 0.12]
    orig = sum(s["duration"] for s in sources)
    new = tl.total_duration(segments)
    report = {
        "level": level,
        "original_duration": round(orig, 2),
        "new_duration": round(new, 2),
        "removed_pct": round(100 * (1 - new / orig), 1) if orig else 0,
        "segments": len(segments),
        "fillers_removed": [f"{w['w']}@{w['s']:.2f}" for w in removed_fillers],
    }
    return segments, report


def autozoom(segments: list[dict], words: list[dict], factor: float = 1.12, max_len: float = 4.5) -> list[dict]:
    """Stile jump-cut: alterna inquadratura normale/punch-in; spezza i segmenti lunghi a una pausa tra parole."""
    def split(p: dict) -> list[dict]:
        if p["out"] - p["in"] <= max_len:
            return [dict(p)]
        mid = (p["in"] + p["out"]) / 2
        gaps = [(words[i]["e"] + words[i + 1]["s"]) / 2 for i in range(len(words) - 1)
                if words[i]["src"] == p["src"] == words[i + 1]["src"]
                and p["in"] + 1.2 < words[i]["e"] and words[i + 1]["s"] < p["out"] - 1.2]
        cut = round(min(gaps, key=lambda g: abs(g - mid)) if gaps else mid, 3)
        a, b = dict(p), dict(p)
        a["out"], b["in"] = cut, cut
        return split(a) + split(b)

    out: list[dict] = []
    for s in segments:
        out += split(s)
    for i, s in enumerate(out):
        s["zoom"] = factor if i % 2 == 1 else 1.0
    return out
