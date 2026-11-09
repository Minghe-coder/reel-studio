"""Trascrizione con faster-whisper (CPU) e tempi parola per parola."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from . import config, ff

# Prompt iniziale: spinge Whisper a scrivere anche gli intercalari (così possiamo tagliarli).
IT_PROMPT = "Ehm, allora, cioè, tipo, ehm... Ok. Quindi, praticamente, ehm, vediamo."


def extract_audio(src: Path, dst: Path) -> None:
    ff.run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-map", "0:a:0", "-ac", "1",
            "-ar", "16000", "-c:a", "pcm_s16le", str(dst)])


def transcribe_file(path: Path, src_id: int, model, language: str = "it") -> tuple[list[dict], list[dict]]:
    hot = " ".join(config.glossary()) or None
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        extract_audio(path, wav)
        kwargs = dict(language=language, word_timestamps=True, vad_filter=True,
                      vad_parameters={"min_silence_duration_ms": 300},
                      condition_on_previous_text=False, initial_prompt=IT_PROMPT, beam_size=5)
        if hot:
            kwargs["hotwords"] = hot
        try:
            segments, _info = model.transcribe(str(wav), **kwargs)
        except TypeError:  # versioni vecchie senza hotwords
            kwargs.pop("hotwords", None)
            segments, _info = model.transcribe(str(wav), **kwargs)
        words, sents = [], []
        for seg in segments:
            sents.append({"src": src_id, "s": round(seg.start, 3), "e": round(seg.end, 3), "text": seg.text.strip()})
            for w in seg.words or []:
                txt = w.word.strip()
                if txt:
                    words.append({"src": src_id, "w": txt, "s": round(w.start, 3), "e": round(w.end, 3),
                                  "p": round(w.probability, 3)})
    return words, sents


def fix_word_ends(words: list[dict], silences: dict[int, list[tuple[float, float]]]) -> list[dict]:
    """Whisper allunga la fine delle parole dentro il silenzio successivo: la tagliamo all'inizio del silenzio."""
    for w in words:
        for a, b in silences.get(w["src"], []):
            if w["s"] < a < w["e"]:
                w["e"] = round(max(w["s"] + 0.05, a), 3)
            if w["s"] < b < w["e"] and a <= w["s"]:
                w["s"] = round(min(b, w["e"] - 0.05), 3)
    return words


def run(project: Path, sources: list[dict], model_size: str = "medium", language: str = "it",
        silences: dict | None = None) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("faster-whisper non installato: esegui  pip install -r requirements.txt") from exc
    print(f"Carico il modello Whisper '{model_size}' (la prima volta lo scarica, ~1.5 GB per medium)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    all_words, all_sents = [], []
    for s in sources:
        print(f"Trascrivo {s['path']} ...")
        w, st = transcribe_file(project / s["path"], s["id"], model, language)
        all_words += w
        all_sents += st
    if silences:
        fix_word_ends(all_words, silences)
    data = {"language": language, "model": model_size, "words": all_words, "sentences": all_sents}
    (project / "transcript.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    txt = "\n".join(f"[{x['src']}:{x['s']:7.2f}] {x['text']}" for x in all_sents)
    (project / "transcript.txt").write_text(txt, encoding="utf-8")
    return data


def load(project: Path) -> dict:
    path = project / "transcript.json"
    if not path.exists():
        return {"words": [], "sentences": []}
    return json.loads(path.read_text(encoding="utf-8"))
