"""Mappatura tempi sorgente <-> timeline finale, operazioni sui segmenti, risoluzione anchor."""
from __future__ import annotations

import re
import unicodedata

EPS = 1e-6


def offsets(segments: list[dict]) -> list[float]:
    out, t = [], 0.0
    for s in segments:
        out.append(t)
        t += s["out"] - s["in"]
    return out


def total_duration(segments: list[dict]) -> float:
    return sum(s["out"] - s["in"] for s in segments)


def src_to_out(segments: list[dict], src: int, t: float) -> float | None:
    """Tempo sorgente -> tempo di uscita (None se quella parte è stata tagliata)."""
    for off, s in zip(offsets(segments), segments):
        if s["src"] == src and s["in"] - EPS <= t < s["out"] + EPS:
            return off + max(0.0, t - s["in"])
    return None


def out_to_src(segments: list[dict], t: float) -> tuple[int, int, float]:
    """Tempo di uscita -> (indice segmento, id sorgente, tempo sorgente)."""
    for i, (off, s) in enumerate(zip(offsets(segments), segments)):
        d = s["out"] - s["in"]
        if off - EPS <= t < off + d - EPS or i == len(segments) - 1:
            return i, s["src"], s["in"] + min(max(0.0, t - off), d)
    raise ValueError("timeline vuota")


def split_at(segments: list[dict], t: float) -> list[dict]:
    """Divide il segmento che contiene il tempo di uscita t."""
    res = []
    for off, s in zip(offsets(segments), segments):
        d = s["out"] - s["in"]
        if off + 0.02 < t < off + d - 0.02:
            cut = s["in"] + (t - off)
            a, b = dict(s), dict(s)
            a["out"], b["in"] = cut, cut
            res += [a, b]
        else:
            res.append(dict(s))
    return res


def cut_out(segments: list[dict], t0: float, t1: float) -> list[dict]:
    """Rimuove l'intervallo [t0, t1) della timeline di uscita."""
    segs = split_at(split_at(segments, t0), t1)
    res = []
    for off, s in zip(offsets(segs), segs):
        d = s["out"] - s["in"]
        if off >= t0 - 0.02 and off + d <= t1 + 0.02:
            continue
        res.append(s)
    return res


def remove_src_range(segments: list[dict], src: int, a: float, b: float) -> list[dict]:
    """Rimuove un intervallo di tempo sorgente da tutti i segmenti che lo contengono."""
    res = []
    for s in segments:
        if s["src"] != src or s["out"] <= a or s["in"] >= b:
            res.append(dict(s))
            continue
        if s["in"] < a - 0.03:
            x = dict(s); x["out"] = a; res.append(x)
        if s["out"] > b + 0.03:
            y = dict(s); y["in"] = b; res.append(y)
    return res


def set_zoom(segments: list[dict], t0: float, t1: float, factor: float, **extra) -> list[dict]:
    segs = split_at(split_at(segments, t0), t1)
    for off, s in zip(offsets(segs), segs):
        mid = off + (s["out"] - s["in"]) / 2
        if t0 <= mid < t1:
            s["zoom"] = factor
            s.update(extra)
    return segs


def move_block(segments: list[dict], t0: float, t1: float, dest: float) -> list[dict]:
    """Sposta il blocco [t0,t1) della timeline di uscita al tempo dest (timeline originale)."""
    segs = split_at(split_at(split_at(segments, t0), t1), dest)
    offs = offsets(segs)
    block = [s for o, s in zip(offs, segs) if t0 - 0.02 <= o < t1 - 0.02]
    rest = [(o, s) for o, s in zip(offs, segs) if not (t0 - 0.02 <= o < t1 - 0.02)]
    res, inserted = [], False
    for o, s in rest:
        if not inserted and o >= dest - 0.02:
            res += block; inserted = True
        res.append(s)
    if not inserted:
        res += block
    return res


# ---------- parole e ricerca ----------

def norm(word: str) -> str:
    w = unicodedata.normalize("NFKD", word.lower())
    w = "".join(c for c in w if not unicodedata.combining(c))
    return re.sub(r"[^\w]", "", w)


def find_phrase(words: list[dict], phrase: str) -> list[tuple[int, int]]:
    """Trova tutte le occorrenze di una frase; restituisce coppie (indice prima parola, indice ultima)."""
    target = [norm(w) for w in phrase.split() if norm(w)]
    if not target:
        return []
    keys = [norm(w["w"]) for w in words]
    hits = []
    for i in range(len(words) - len(target) + 1):
        if keys[i:i + len(target)] == target and all(words[i + k]["src"] == words[i]["src"] for k in range(len(target))):
            hits.append((i, i + len(target) - 1))
    return hits


def kept_words(words: list[dict], segments: list[dict]) -> list[dict]:
    """Parole presenti nella timeline finale, con tempi di uscita (os, oe)."""
    res = []
    offs = offsets(segments)
    for w in words:
        mid = (w["s"] + w["e"]) / 2
        for off, s in zip(offs, segments):
            if s["src"] == w["src"] and s["in"] - EPS <= mid < s["out"] + EPS:
                os_ = off + max(0.0, w["s"] - s["in"])
                oe = off + min(s["out"], w["e"]) - s["in"]
                res.append({**w, "os": os_, "oe": max(oe, os_ + 0.05)})
                break
    res.sort(key=lambda x: x["os"])
    return res


def resolve(anchor, segments: list[dict], words: list[dict]) -> float:
    """Converte un anchor (vedi edl.py) in secondi sulla timeline finale."""
    total = total_duration(segments)
    if anchor is None:
        return 0.0
    if isinstance(anchor, (int, float)):
        return max(0.0, total + anchor) if anchor < 0 else float(anchor)
    if isinstance(anchor, str):
        return resolve(float(anchor), segments, words)
    if "from_end" in anchor:
        return max(0.0, total - float(anchor["from_end"]))
    if "word" in anchor:
        kw = kept_words(words, segments)
        hits = find_phrase(kw, anchor["word"])
        n = int(anchor.get("n", 1))
        if not hits or n > len(hits):
            raise ValueError(f"parola/frase non trovata nel montaggio: {anchor['word']!r} (occorrenza {n})")
        i, j = hits[n - 1]
        t = kw[j]["oe"] if anchor.get("edge") == "end" else kw[i]["os"]
        return t + float(anchor.get("offset", 0))
    if "src" in anchor:
        t = src_to_out(segments, int(anchor["src"]), float(anchor["t"]))
        if t is None:
            raise ValueError(f"il tempo sorgente {anchor} è stato tagliato via")
        return t + float(anchor.get("offset", 0))
    if "segment" in anchor:
        return offsets(segments)[int(anchor["segment"])] + float(anchor.get("offset", 0))
    raise ValueError(f"anchor non valido: {anchor}")


def parse_time(value: str) -> float:
    """'1:02.5' -> 62.5 ; '12.3' -> 12.3"""
    value = str(value).strip().replace(",", ".")
    if ":" in value:
        parts = [float(p) for p in value.split(":")]
        t = 0.0
        for p in parts:
            t = t * 60 + p
        return t
    return float(value)


def fmt_time(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m)}:{s:05.2f}"
