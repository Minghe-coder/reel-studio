"""Costruisce ed esegue il comando ffmpeg che trasforma l'EDL nel video finale."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import captions_ass, config, ff
from . import timeline as tl
from . import transcribe as tr


def _hex(c: str) -> str:
    return "0x" + c.lstrip("#")


def resolve_events(edl: dict, words: list[dict]) -> dict:
    """Risolve tutti gli anchor in secondi sulla timeline finale."""
    segs = edl["segments"]
    total = tl.total_duration(segs)
    R = lambda a: tl.resolve(a, segs, words)  # noqa: E731

    def span(ev, default_dur):
        a = R(ev.get("start", ev.get("at", 0)))
        b = R(ev["end"]) if "end" in ev else a + float(ev.get("dur", default_dur))
        return max(0.0, min(a, total)), max(0.0, min(b, total))

    out = {"total": total}
    out["texts"] = [span(t, 2.5) for t in edl.get("texts", [])]
    out["popups"] = [span(p, 1.5) for p in edl.get("popups", [])]
    out["transitions"] = []
    for t in edl.get("transitions", []):
        if "at" in t:
            out["transitions"].append((t, R(t["at"])))
        elif t.get("at_all_cuts"):
            for off in tl.offsets(segs)[1:]:
                out["transitions"].append((t, off))
    sfx = [(s, R(s["at"])) for s in edl.get("sfx", [])]
    # SFX automatici legati a pop-up / transizioni
    for p, (a, _b) in zip(edl.get("popups", []), out["popups"]):
        if p.get("sfx"):
            sfx.append(({"file": p["sfx"], "volume": p.get("sfx_volume", 0.8)}, a))
    for t, at in out["transitions"]:
        if t.get("sfx"):
            sfx.append(({"file": t["sfx"], "volume": t.get("sfx_volume", 0.7)}, max(0.0, at - t.get("sfx_lead", 0.15))))
    out["sfx"] = sfx
    return out


def caption_emoji_popups(edl: dict, words: list[dict]) -> list[dict]:
    """Le emoji dei sottotitoli (captions.emoji) diventano pop-up PNG: libass non disegna emoji a colori."""
    from . import assets
    emap = {tl.norm(k): v for k, v in ((edl.get("captions") or {}).get("emoji") or {}).items()}
    if not emap or not (edl.get("captions") or {}).get("enabled", True):
        return []
    y = (config.caption_presets().get(edl["captions"].get("preset", "bold"), {}) or {}).get("y", 1250)
    pops = []
    for w in tl.kept_words(words, edl["segments"]):
        em = emap.get(tl.norm(w["w"]))
        if em:
            img = assets.emoji_png(em).relative_to(config.ROOT).as_posix()
            pops.append({"image": img, "start": w["os"], "dur": max(0.8, w["oe"] - w["os"] + 0.5),
                         "x": "center", "y": y - 230, "width": 170, "anim": "pop"})
    return pops


def build_command(project: Path, edl: dict, out_file: Path, preview: bool = False) -> tuple[list[str], str]:
    exp = config.export_cfg()
    W, H, FPS = exp["width"], exp["height"], exp["fps"]
    words = tr.load(project).get("words", [])
    segs = edl["segments"]
    if not segs:
        raise SystemExit("EDL senza segmenti: esegui prima `python -m reel ingest` o `autocut`.")
    edl = {**edl, "popups": list(edl.get("popups", [])) + caption_emoji_popups(edl, words)}
    ev = resolve_events(edl, words)
    total = ev["total"]
    srcs = {s["id"]: s for s in edl["sources"]}
    root = config.ROOT

    def asset(p: str) -> str:
        cand = [project / p, root / p, root / "assets" / p]
        for c in cand:
            if c.exists():
                return str(c.resolve())
        raise SystemExit(f"File non trovato: {p}")

    inputs: list[str] = []
    fc: list[str] = []
    n_in = 0

    # 1) un input per segmento (seek veloce), normalizzato a 1080x1920 @30fps
    vlabels, alabels = [], []
    for i, s in enumerate(segs):
        src = srcs[s["src"]]
        d = s["out"] - s["in"]
        inputs += ["-ss", f"{s['in']:.3f}", "-t", f"{d:.3f}", "-i", str((project / src["path"]).resolve())]
        z = float(s.get("zoom", 1.0) or 1.0)
        cy = s.get("focus_y", 0.42)  # punto verticale da tenere (0 alto, 1 basso): volti di solito in alto
        cx = s.get("focus_x", 0.5)
        v = (f"[{n_in}:v]setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},setsar=1")
        if abs(z - 1.0) > 1e-3:
            zw, zh = int(round(W * z / 2) * 2), int(round(H * z / 2) * 2)
            v += f",scale={zw}:{zh},crop={W}:{H}:(iw-ow)*{cx}:(ih-oh)*{cy}"
        v += f",setsar=1,trim=duration={d:.3f}[v{i}]"
        fc.append(v)
        if src.get("has_audio", True):
            fd = min(0.012, d / 4)
            fc.append(f"[{n_in}:a]asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=mono,"
                      f"atrim=duration={d:.3f},afade=t=in:d={fd:.3f},afade=t=out:st={d - fd:.3f}:d={fd:.3f}[a{i}]")
        else:
            fc.append(f"anullsrc=r=48000:cl=mono,atrim=duration={d:.3f}[a{i}]")
        vlabels.append(f"[v{i}]")
        alabels.append(f"[a{i}]")
        n_in += 1
    fc.append("".join(v + a for v, a in zip(vlabels, alabels)) + f"concat=n={len(segs)}:v=1:a=1[vc][ac]")

    # 2) colore
    vcur = "vc"
    col = edl.get("color", {}) or {}
    vf = []
    if col.get("lut"):
        lut = Path(shutil.os.path.relpath(asset(col["lut"]), project)).as_posix()
        vf.append(f"lut3d='{lut}'")
    if any(abs(col.get(k, d) - d) > 1e-3 for k, d in (("saturation", 1), ("contrast", 1), ("brightness", 0))):
        vf.append(f"eq=saturation={col.get('saturation', 1)}:contrast={col.get('contrast', 1)}:brightness={col.get('brightness', 0)}")
    if vf:
        fc.append(f"[{vcur}]{','.join(vf)}[vcol]")
        vcur = "vcol"

    # 3) pop-up immagini (png/emoji) con animazione
    for k, (p, (a, b)) in enumerate(zip(edl.get("popups", []), ev["popups"])):
        dur = max(0.2, b - a)
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", asset(p["image"])]
        pw = int(p.get("width", 420))
        anim = p.get("anim", "pop")
        if anim == "pop":
            # pop: da 40% a 110% in 0.12s, poi assestamento al 100%
            sc = (f"scale=w='{pw}*if(lt(t,0.12),0.4+5.83*t,if(lt(t,0.2),1.1-1.25*(t-0.12),1))':h=-1:eval=frame")
        else:
            sc = f"scale={pw}:-1"
        fo = max(0.0, dur - 0.15)
        fc.append(f"[{n_in}:v]format=rgba,{sc},fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={fo:.3f}:d=0.15:alpha=1,"
                  f"setpts=PTS-STARTPTS+{a:.3f}/TB[pp{k}]")
        x = p.get("x", "center")
        y = p.get("y", 760)
        xe = "(W-w)/2" if x == "center" else str(x)
        ye = "(H-h)/2" if y == "center" else f"{y}-h/2"
        if anim == "slide":
            xe = f"if(lt(t-{a:.3f},0.2),W-(W-({xe}))*(t-{a:.3f})/0.2,{xe})"
        fc.append(f"[{vcur}][pp{k}]overlay=x='{xe}':y='{ye}':eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[vp{k}]")
        vcur = f"vp{k}"
        n_in += 1

    # 4) transizioni visive (flash / zoom-blur leggero)
    draws = []
    for t, at in ev["transitions"]:
        typ = t.get("type", "flash")
        if typ == "flash":
            d = t.get("dur", 0.12)
            c = t.get("color", "#FFFFFF")
            draws.append(f"drawbox=x=0:y=0:w=iw:h=ih:color={_hex(c)}@{t.get('opacity', 0.85)}:t=fill:"
                         f"enable='between(t,{at:.3f},{at + d:.3f})'")
        elif typ == "dip":
            d = t.get("dur", 0.2)
            draws.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.9:t=fill:enable='between(t,{at - d / 2:.3f},{at + d / 2:.3f})'")
    pb = edl.get("progress_bar", {}) or {}
    if pb.get("enabled"):
        color = pb.get("color") or config.brand().get("progress_bar_color", "#FFD400")
        h = int(pb.get("height", 12))
        ypos = pb.get("y", "ih-" + str(h + 6)) if pb.get("position", "top") == "bottom" else str(pb.get("y", 0))
        draws.append(f"drawbox=x=0:y={ypos}:w='iw*t/{total:.3f}':h={h}:color={_hex(color)}@1:t=fill")
    if draws:
        fc.append(f"[{vcur}]{','.join(draws)}[vd]")
        vcur = "vd"

    # 5) sottotitoli + testi (file ASS)
    kw = tl.kept_words(words, segs)
    ass = captions_ass.build(edl, kw, ev["texts"])
    out_dir = project / "out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "captions.ass").write_text(ass, encoding="utf-8")
    fonts_rel = Path("..") / ".." / "assets" / "fonts"
    if not (project / fonts_rel).exists():
        fonts_rel = Path(shutil.os.path.relpath(config.FONTS, project))
    # percorsi relativi (cwd = cartella progetto): evita i problemi con 'C:' su Windows
    fc.append(f"[{vcur}]subtitles=out/captions.ass:fontsdir={fonts_rel.as_posix()}[vs]")
    vcur = "vs"
    if preview:
        pv = exp["preview"]
        fc.append(f"[{vcur}]scale={pv['width']}:{pv['height']},format=yuv420p[vout]")
    else:
        fc.append(f"[{vcur}]format=yuv420p[vout]")

    # 6) audio: voce -> musica con ducking -> sfx -> loudness
    au = edl.get("audio", {}) or {}
    chain = ["highpass=f=80"]
    if au.get("denoise", True):
        chain.append("afftdn=nf=-25:tn=1")
    if au.get("voice_eq", True):
        chain += ["equalizer=f=250:t=q:w=1:g=-2", "equalizer=f=3500:t=q:w=1.2:g=3"]
    if au.get("compress", True):
        chain.append("acompressor=threshold=0.1:ratio=3:attack=5:release=80:makeup=2")
    fc.append(f"[ac]{','.join(chain)}[voice]")
    mix = ["[voice]"]
    mu = edl.get("music", {}) or {}
    if mu.get("file"):
        inputs += ["-stream_loop", "-1", "-i", asset(mu["file"])]
        mstart = float(mu.get("start", 0))
        fin, fout = mu.get("fade_in", 0.5), mu.get("fade_out", 1.5)
        fc.append(f"[{n_in}:a]atrim=start={mstart}:duration={total:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                  f"aformat=channel_layouts=stereo,volume={mu.get('volume', 0.15)},afade=t=in:d={fin},"
                  f"afade=t=out:st={max(0, total - fout):.3f}:d={fout}[mus]")
        n_in += 1
        if mu.get("duck", True):
            fc.append("[voice]asplit=2[voice][vsc]")
            fc.append("[mus][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350:makeup=1[musd]")
            mix.append("[musd]")
        else:
            mix.append("[mus]")
    for k, (s, at) in enumerate(ev["sfx"]):
        inputs += ["-i", asset(s["file"])]
        ms = int(round(at * 1000))
        fc.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,volume={s.get('volume', 0.8)},"
                  f"adelay={ms}|{ms}[sfx{k}]")
        mix.append(f"[sfx{k}]")
        n_in += 1
    loud = f"loudnorm=I={exp['loudness_lufs']}:TP={exp['true_peak_db']}:LRA=11"
    if len(mix) > 1:
        fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:dropout_transition=0:normalize=0,"
                  f"{loud},aresample=48000,atrim=duration={total:.3f}[aout]")
    else:
        fc.append(f"[voice]{loud},aresample=48000,atrim=duration={total:.3f}[aout]")

    script = ";\n".join(fc)
    (out_dir / "filtergraph.txt").write_text(script, encoding="utf-8")
    if preview:
        vopts = ["-c:v", "libx264", "-preset", exp["preview"]["preset"], "-crf", str(exp["preview"]["crf"])]
    else:
        vopts = ["-c:v", exp["video_codec"], "-preset", exp["preset"], "-crf", str(exp["crf"]),
                 "-maxrate", exp["maxrate"], "-bufsize", exp["bufsize"], "-profile:v", "high", "-level", "4.2"]
    fc_opt = ["-/filter_complex", "out/filtergraph.txt"] if ff.version()[0] >= 7 else ["-filter_complex_script", "out/filtergraph.txt"]
    cmd = ["ffmpeg", "-y", "-hide_banner", *inputs, *fc_opt,
           "-map", "[vout]", "-map", "[aout]", *vopts, "-r", str(FPS), "-pix_fmt", "yuv420p",
           "-c:a", exp["audio_codec"], "-b:a", exp["audio_bitrate"], "-ar", str(exp["sample_rate"]),
           "-movflags", "+faststart", "-t", f"{total:.3f}", str(out_file.relative_to(project).as_posix()
                                                                    if out_file.is_relative_to(project) else out_file)]
    return cmd, script


def correct_loudness(project: Path, out_file: Path) -> dict:
    """Secondo passaggio: se la loudness misurata è fuori di >0.7 LU, corregge il guadagno (video copiato)."""
    exp = config.export_cfg()
    m = ff.measure_loudness(out_file)
    target = exp["loudness_lufs"]
    if m["integrated"] is None or abs(m["integrated"] - target) <= 0.7:
        return m
    gain = target - m["integrated"]
    tmp = out_file.with_suffix(".tmp.mp4")
    ff.run(["ffmpeg", "-y", "-hide_banner", "-i", str(out_file), "-c:v", "copy",
            "-af", f"volume={gain:.2f}dB,alimiter=limit={10 ** (exp['true_peak_db'] / 20):.3f}:level=false",
            "-c:a", exp["audio_codec"], "-b:a", exp["audio_bitrate"], "-movflags", "+faststart", str(tmp)])
    tmp.replace(out_file)
    return ff.measure_loudness(out_file)


def render(project: Path, edl: dict, preview: bool = False, name: str | None = None) -> Path:
    out_dir = project / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / (name or ("preview.mp4" if preview else "final.mp4"))
    cmd, _ = build_command(project, edl, out_file, preview=preview)
    (out_dir / "last_command.json").write_text(json.dumps(cmd, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Render {'anteprima' if preview else 'finale'} in corso ({tl.fmt_time(tl.total_duration(edl['segments']))})...")
    ff.run(cmd, cwd=project)
    if not preview:
        m = correct_loudness(project, out_file)
        print(f"Loudness: {m['integrated']} LUFS, true peak {m['true_peak']} dBTP")
    return out_file
