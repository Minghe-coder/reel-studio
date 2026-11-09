"""Riga di comando: python -m reel <comando> <progetto> [opzioni]

Claude Code usa questi comandi al posto tuo; puoi usarli anche a mano.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, edl as E, ff
from . import timeline as tl


def P(name: str) -> Path:
    p = config.project_dir(name)
    if not p.exists():
        raise SystemExit(f"Progetto '{name}' non trovato in {config.PROJECTS}. Crealo con: python -m reel new {name}")
    return p


def parse_anchor(s: str):
    """'12.5' | '-3' (dalla fine) | '1:02.5' | 'parola:gratis' | 'parola:in regalo#2' | 'fine:gratis' | 'seg:3' | 'src:0@12.3'"""
    s = s.strip()
    for prefix, edge in (("parola:", None), ("word:", None), ("fine:", "end"), ("end:", "end")):
        if s.lower().startswith(prefix):
            body = s[len(prefix):]
            n = 1
            if "#" in body:
                body, n = body.rsplit("#", 1)
            a = {"word": body.strip(), "n": int(n)}
            if edge:
                a["edge"] = edge
            return a
    if s.lower().startswith("seg:"):
        return {"segment": int(s[4:])}
    if s.lower().startswith("src:"):
        sid, t = s[4:].split("@")
        return {"src": int(sid), "t": tl.parse_time(t)}
    if s.startswith("-"):
        return {"from_end": tl.parse_time(s[1:])}
    return tl.parse_time(s)


def _rel(path: str) -> str:
    """Percorsi dentro il progetto/la cartella principale salvati come relativi (portabili)."""
    p = Path(path).resolve()
    if p.is_relative_to(config.ROOT):
        return p.relative_to(config.ROOT).as_posix()
    return Path(path).as_posix()


def _words(project: Path) -> list[dict]:
    from . import transcribe as tr
    return tr.load(project).get("words", [])


def _out_time(arg: str, project: Path, edl: dict) -> float:
    return tl.resolve(parse_anchor(arg), edl["segments"], _words(project))


def _silences(project: Path, edl: dict, threshold=None, min_dur=0.2, refresh=False) -> dict[int, list]:
    from . import silence
    cache = project / "silences.json"
    if cache.exists() and not refresh:
        return {int(k): [tuple(x) for x in v] for k, v in json.loads(cache.read_text()).items()}
    res = {}
    for s in edl["sources"]:
        if s.get("has_audio", True):
            res[s["id"]] = silence.detect(project / s["path"], threshold, min_dur)
    cache.write_text(json.dumps(res))
    return res


# ---------------- comandi ----------------

def cmd_doctor(a):
    from . import doctor
    sys.exit(0 if doctor.run() else 1)


def cmd_new(a):
    from . import project
    p = project.create(a.project)
    print(f"Progetto creato: {p}\n  1) copia i video in {p / 'raw'}\n  2) python -m reel ingest {a.project}")


def cmd_ingest(a):
    from . import project
    project.ingest(P(a.project), a.files, a.normalize)


def cmd_transcribe(a):
    from . import transcribe
    p = P(a.project)
    edl = E.load(p)
    sil = _silences(p, edl, refresh=True)
    data = transcribe.run(p, edl["sources"], a.model, a.language, sil)
    print(f"{len(data['words'])} parole trascritte -> {p / 'transcript.txt'}")


def cmd_autocut(a):
    from . import cuts
    p = P(a.project)
    edl = E.load(p)
    sil = _silences(p, edl, a.threshold, 0.2, refresh=a.threshold is not None)
    segs, rep = cuts.autocut(edl["sources"], sil, _words(p), a.level, not a.keep_fillers)
    edl["segments"] = segs
    E.save(p, edl)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if rep["removed_pct"] > 45:
        print("ATTENZIONE: tagliato più del 45%: controlla l'anteprima (magari usa --level leggero).")


def cmd_autozoom(a):
    from . import cuts
    p = P(a.project)
    edl = E.load(p)
    edl["segments"] = cuts.autozoom(edl["segments"], _words(p), a.factor, a.max_len)
    E.save(p, edl)
    print(f"{len(edl['segments'])} inquadrature, punch-in {a.factor}x a segmenti alterni")


def cmd_cut(a):
    p = P(a.project)
    edl = E.load(p)
    words = _words(p)
    if a.phrase:
        hits = tl.find_phrase(words, a.phrase)
        if not hits:
            raise SystemExit(f"Frase non trovata: {a.phrase!r}")
        chosen = hits if a.all else [hits[(a.n or 1) - 1]]
        for i, j in chosen:
            edl["segments"] = tl.remove_src_range(edl["segments"], words[i]["src"], words[i]["s"] - 0.04, words[j]["e"] + 0.04)
        print(f"Rimosse {len(chosen)} occorrenze di {a.phrase!r}")
    else:
        t0, t1 = _out_time(a.start, p, edl), _out_time(a.end, p, edl)
        edl["segments"] = tl.cut_out(edl["segments"], t0, t1)
        print(f"Tagliato {tl.fmt_time(t0)} -> {tl.fmt_time(t1)}")
    E.save(p, edl)
    print(f"Nuova durata: {tl.fmt_time(tl.total_duration(edl['segments']))}")


def cmd_trim(a):
    """Accorcia/allunga un segmento di N secondi all'inizio o alla fine (valori negativi = allunga)."""
    p = P(a.project)
    edl = E.load(p)
    s = edl["segments"][a.segment]
    src = next(x for x in edl["sources"] if x["id"] == s["src"])
    s["in"] = round(min(max(0.0, s["in"] + a.head), s["out"] - 0.1), 3)
    s["out"] = round(max(min(src["duration"], s["out"] - a.tail), s["in"] + 0.1), 3)
    E.save(p, edl)
    print(f"segmento {a.segment}: {s['in']:.2f}–{s['out']:.2f}")


def cmd_find(a):
    p = P(a.project)
    edl = E.load(p)
    words = _words(p)
    kw = tl.kept_words(words, edl["segments"])
    for k, (i, j) in enumerate(tl.find_phrase(words, a.text), 1):
        out = tl.src_to_out(edl["segments"], words[i]["src"], (words[i]["s"] + words[i]["e"]) / 2)
        where = f"uscita {tl.fmt_time(out)}" if out is not None else "TAGLIATA"
        print(f"#{k}: src{words[i]['src']} {words[i]['s']:.2f}-{words[j]['e']:.2f}s  ({where})")
    if not kw:
        print("(nessuna trascrizione: esegui transcribe)")


def cmd_zoom(a):
    p = P(a.project)
    edl = E.load(p)
    t0, t1 = _out_time(a.start, p, edl), _out_time(a.end, p, edl)
    extra = {}
    if a.focus_y is not None:
        extra["focus_y"] = a.focus_y
    edl["segments"] = tl.set_zoom(edl["segments"], t0, t1, a.factor, **extra)
    E.save(p, edl)
    print(f"Zoom {a.factor}x da {tl.fmt_time(t0)} a {tl.fmt_time(t1)}")


def cmd_move(a):
    p = P(a.project)
    edl = E.load(p)
    t0, t1, d = (_out_time(x, p, edl) for x in (a.start, a.end, a.dest))
    edl["segments"] = tl.move_block(edl["segments"], t0, t1, d)
    E.save(p, edl)
    print("Blocco spostato")


def cmd_text(a):
    p = P(a.project)
    edl = E.load(p)
    ev = {"text": a.text.replace("\\n", "\n"), "start": parse_anchor(a.at), "style": a.style}
    if a.end:
        ev["end"] = parse_anchor(a.end)
    else:
        ev["dur"] = a.dur
    if a.y is not None:
        ev["y"] = a.y
    if a.anim:
        ev["anim"] = a.anim
    edl["texts"].append(ev)
    tl.resolve(ev["start"], edl["segments"], _words(p))  # verifica subito
    E.save(p, edl)
    print(f"Testo aggiunto ({a.style}): {a.text}")


def cmd_popup(a):
    from . import assets
    p = P(a.project)
    edl = E.load(p)
    if a.emoji:
        img = assets.emoji_png(a.emoji).relative_to(config.ROOT).as_posix()
    else:
        img = _rel(a.image)
    ev = {"image": img, "start": parse_anchor(a.at), "dur": a.dur, "x": a.x if a.x == "center" else int(a.x),
          "y": a.y if a.y == "center" else int(a.y), "width": a.width, "anim": a.anim}
    if a.sfx:
        ev["sfx"] = a.sfx
    tl.resolve(ev["start"], edl["segments"], _words(p))
    edl["popups"].append(ev)
    E.save(p, edl)
    print(f"Pop-up aggiunto: {img}")


def cmd_sfx(a):
    p = P(a.project)
    edl = E.load(p)
    ev = {"file": _rel(a.file) if Path(a.file).exists() else a.file, "at": parse_anchor(a.at), "volume": a.volume}
    tl.resolve(ev["at"], edl["segments"], _words(p))
    edl["sfx"].append(ev)
    E.save(p, edl)
    print(f"SFX aggiunto: {a.file}")


def cmd_transition(a):
    p = P(a.project)
    edl = E.load(p)
    ev = {"type": a.type}
    if a.all_cuts:
        ev["at_all_cuts"] = True
    else:
        ev["at"] = parse_anchor(a.at)
    if a.sfx:
        ev["sfx"] = a.sfx
    edl["transitions"].append(ev)
    E.save(p, edl)
    print(f"Transizione {a.type} aggiunta")


def cmd_music(a):
    p = P(a.project)
    edl = E.load(p)
    if a.off:
        edl["music"]["file"] = None
    else:
        edl["music"].update({"file": _rel(a.file), "volume": a.volume, "duck": not a.no_duck, "start": a.start})
    E.save(p, edl)
    print("Musica: " + (edl["music"]["file"] or "nessuna"))


def cmd_captions(a):
    p = P(a.project)
    edl = E.load(p)
    c = edl["captions"]
    if a.off:
        c["enabled"] = False
    else:
        c["enabled"] = True
    if a.preset:
        if a.preset not in config.caption_presets():
            raise SystemExit(f"Preset sconosciuto. Disponibili: {', '.join(config.caption_presets())}")
        c["preset"] = a.preset
    if a.highlight:
        c["highlight_words"] = sorted(set(c.get("highlight_words", [])) | set(a.highlight))
    for r in a.replace or []:
        k, v = r.split("=", 1)
        c.setdefault("replacements", {})[k.strip()] = v.strip()
    for r in a.emoji or []:
        k, v = r.split("=", 1)
        c.setdefault("emoji", {})[k.strip()] = v.strip()
    E.save(p, edl)
    print(json.dumps(c, indent=1, ensure_ascii=False))


def cmd_progress(a):
    p = P(a.project)
    edl = E.load(p)
    edl["progress_bar"]["enabled"] = a.state == "on"
    if a.position:
        edl["progress_bar"]["position"] = a.position
    E.save(p, edl)
    print(f"Barra di avanzamento: {a.state}")


def cmd_show(a):
    p = P(a.project)
    edl = E.load(p)
    words = _words(p)
    kw = tl.kept_words(words, edl["segments"])
    print(f"Durata finale: {tl.fmt_time(tl.total_duration(edl['segments']))}  ·  segmenti: {len(edl['segments'])}")
    for i, (off, s) in enumerate(zip(tl.offsets(edl["segments"]), edl["segments"])):
        d = s["out"] - s["in"]
        txt = " ".join(w["w"] for w in kw if off - 1e-6 <= w["os"] < off + d - 1e-6)
        z = f" zoom{s['zoom']}" if s.get("zoom", 1) != 1 else ""
        print(f"[{i:02d}] {tl.fmt_time(off)}–{tl.fmt_time(off + d)}  src{s['src']} {s['in']:.2f}-{s['out']:.2f}{z} | {txt}")
    for key in ("texts", "popups", "transitions", "sfx"):
        if edl.get(key):
            print(f"{key}: " + json.dumps(edl[key], ensure_ascii=False))
    print(f"music: {edl['music']}  ·  captions: {edl['captions']['preset'] if edl['captions']['enabled'] else 'off'}")
    errs = E.validate(edl)
    if errs:
        print("PROBLEMI: " + "; ".join(errs))


def cmd_remove(a):
    p = P(a.project)
    edl = E.load(p)
    item = edl[a.kind].pop(a.index)
    E.save(p, edl)
    print(f"Rimosso da {a.kind}: {item}")


def cmd_render(a, preview=False):
    from . import qc, render
    p = P(a.project)
    edl = E.load(p)
    errs = E.validate(edl)
    if errs:
        raise SystemExit("EDL non valido: " + "; ".join(errs))
    out = render.render(p, edl, preview=preview or a.preview, name=a.name)
    print(f"Fatto: {out}")
    if not (preview or a.preview):
        rep = qc.check(p, out)
        print(json.dumps(rep, indent=1, ensure_ascii=False))


def cmd_qc(a):
    from . import qc
    p = P(a.project)
    print(json.dumps(qc.check(p, p / "out" / (a.file or "final.mp4")), indent=1, ensure_ascii=False))


def cmd_undo(a):
    p = P(a.project)
    print("Annullata l'ultima modifica" if E.undo(p) else "Niente da annullare")


def cmd_sfx_base(a):
    from . import assets
    made = assets.make_basic_sfx(a.overwrite)
    print(f"Creati {len(made)} effetti di base in assets/sfx")
    print(assets.catalog())


def cmd_catalog(a):
    from . import assets
    print(assets.catalog())


def cmd_emoji(a):
    from . import assets
    print(assets.emoji_png(a.char))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="reel", description="Montaggio video verticali (IG Reels / TikTok)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def sp(name, fn, help_, project=True):
        x = sub.add_parser(name, help=help_)
        if project:
            x.add_argument("project")
        x.set_defaults(fn=fn)
        return x

    sp("doctor", cmd_doctor, "controlla l'installazione", project=False)
    sp("new", cmd_new, "crea un nuovo progetto")
    x = sp("ingest", cmd_ingest, "importa i video di raw/")
    x.add_argument("--files", nargs="*")
    x.add_argument("--normalize", action="store_true")
    x = sp("transcribe", cmd_transcribe, "trascrive con Whisper (tempi parola per parola)")
    x.add_argument("--model", default="medium", help="tiny|base|small|medium|large-v3")
    x.add_argument("--language", default="it")
    x = sp("autocut", cmd_autocut, "taglio automatico di silenzi e intercalari")
    x.add_argument("--level", choices=["leggero", "normale", "aggressivo"], default="normale")
    x.add_argument("--keep-fillers", action="store_true")
    x.add_argument("--threshold", type=float, help="soglia silenzio in dB (es. -35); default automatica")
    x = sp("autozoom", cmd_autozoom, "punch-in alternati stile jump-cut")
    x.add_argument("--factor", type=float, default=1.12)
    x.add_argument("--max-len", type=float, default=4.5)
    x = sp("cut", cmd_cut, "taglia un intervallo (tempi finali) o una frase")
    x.add_argument("--from", dest="start")
    x.add_argument("--to", dest="end")
    x.add_argument("--phrase")
    x.add_argument("--n", type=int, help="quale occorrenza della frase (1 = prima)")
    x.add_argument("--all", action="store_true")
    x = sp("trim", cmd_trim, "rifila inizio/fine di un segmento")
    x.add_argument("segment", type=int)
    x.add_argument("--head", type=float, default=0.0)
    x.add_argument("--tail", type=float, default=0.0)
    x = sp("find", cmd_find, "trova quando dici una parola/frase")
    x.add_argument("text")
    x = sp("zoom", cmd_zoom, "zoom statico in un intervallo")
    x.add_argument("--from", dest="start", required=True)
    x.add_argument("--to", dest="end", required=True)
    x.add_argument("--factor", type=float, default=1.2)
    x.add_argument("--focus-y", type=float)
    x = sp("move", cmd_move, "sposta un blocco")
    x.add_argument("--from", dest="start", required=True)
    x.add_argument("--to", dest="end", required=True)
    x.add_argument("--dest", required=True)
    x = sp("text", cmd_text, "testo a schermo (hook, title, cta, label, number)")
    x.add_argument("text")
    x.add_argument("--at", required=True)
    x.add_argument("--end")
    x.add_argument("--dur", type=float, default=2.5)
    x.add_argument("--style", default="hook")
    x.add_argument("--y", type=int)
    x.add_argument("--anim", choices=["pop", "fade", "slide", "typewriter"])
    x = sp("popup", cmd_popup, "pop-up immagine o emoji")
    g = x.add_mutually_exclusive_group(required=True)
    g.add_argument("--image")
    g.add_argument("--emoji")
    x.add_argument("--at", required=True)
    x.add_argument("--dur", type=float, default=1.5)
    x.add_argument("--x", default="center")
    x.add_argument("--y", default="760")
    x.add_argument("--width", type=int, default=380)
    x.add_argument("--anim", choices=["pop", "fade", "slide"], default="pop")
    x.add_argument("--sfx")
    x = sp("sfx", cmd_sfx, "effetto sonoro")
    x.add_argument("file")
    x.add_argument("--at", required=True)
    x.add_argument("--volume", type=float, default=0.8)
    x = sp("transition", cmd_transition, "transizione (flash, dip, none+sfx)")
    x.add_argument("--type", choices=["flash", "dip", "none"], default="flash")
    x.add_argument("--at")
    x.add_argument("--all-cuts", action="store_true")
    x.add_argument("--sfx")
    x = sp("music", cmd_music, "musica di sottofondo")
    x.add_argument("file", nargs="?")
    x.add_argument("--volume", type=float, default=0.15)
    x.add_argument("--no-duck", action="store_true")
    x.add_argument("--start", type=float, default=0.0, help="da che secondo del brano partire")
    x.add_argument("--off", action="store_true")
    x = sp("captions", cmd_captions, "sottotitoli")
    x.add_argument("--preset")
    x.add_argument("--highlight", nargs="*")
    x.add_argument("--replace", nargs="*", help="sbagliato=giusto")
    x.add_argument("--emoji", nargs="*", help="parola=🔥")
    x.add_argument("--off", action="store_true")
    x = sp("progress", cmd_progress, "barra di avanzamento on/off")
    x.add_argument("state", choices=["on", "off"])
    x.add_argument("--position", choices=["top", "bottom"])
    sp("show", cmd_show, "riepilogo del montaggio")
    x = sp("remove", cmd_remove, "rimuove un elemento (texts/popups/sfx/transitions)")
    x.add_argument("kind", choices=["texts", "popups", "sfx", "transitions"])
    x.add_argument("index", type=int)
    for name, prev in (("preview", True), ("render", False)):
        x = sp(name, lambda a, pv=prev: cmd_render(a, pv), "anteprima veloce 540p" if prev else "render finale 1080x1920 + QC")
        x.add_argument("--name")
        x.add_argument("--preview", action="store_true", help=argparse.SUPPRESS)
    x = sp("qc", cmd_qc, "controllo qualità")
    x.add_argument("--file")
    sp("undo", cmd_undo, "annulla l'ultima modifica all'EDL")
    x = sp("sfx-base", cmd_sfx_base, "genera effetti sonori di base", project=False)
    x.add_argument("--overwrite", action="store_true")
    sp("catalog", cmd_catalog, "aggiorna i cataloghi di musica e SFX", project=False)
    x = sp("emoji", cmd_emoji, "scarica un'emoji come PNG", project=False)
    x.add_argument("char")
    return ap


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except ff.FFmpegError as exc:
        raise SystemExit(f"Errore FFmpeg:\n{exc}") from exc
    except ValueError as exc:
        raise SystemExit(f"Errore: {exc}") from exc
