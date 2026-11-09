"""Genera il file .ass (sottotitoli + testi a schermo) sulla tela 1080x1920."""
from __future__ import annotations

from . import config
from . import timeline as tl

W, H = 1080, 1920


def ass_color(hex_color: str, alpha: float = 0.0) -> str:
    """#RRGGBB -> &HAABBGGRR (alpha 0 = opaco)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    a = int(round(alpha * 255))
    return f"&H{a:02X}{b}{g}{r}".upper()


def inline_color(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def style_line(name: str, font: str, size: int, color: str, outline_color: str, outline: float,
               shadow: float, box: bool, box_color: str = "#000000", box_alpha: float = 0.5) -> str:
    border_style = 3 if box else 1
    back = ass_color(box_color, 1 - box_alpha) if box else ass_color("#000000", 0.4)
    outc = ass_color(box_color, 1 - box_alpha) if box else ass_color(outline_color)
    ol = max(outline, 14) if box else outline
    return (f"Style: {name},{font},{size},{ass_color(color)},{ass_color(color)},{outc},{back},"
            f"0,0,0,0,100,100,0,0,{border_style},{ol},{shadow},5,60,150,60,1")


def group_words(words: list[dict], max_words: int, max_chars: int, max_gap: float = 0.6) -> list[list[dict]]:
    """Raggruppa le parole in blocchi brevi, spezzando su pause e punteggiatura."""
    groups: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        text = " ".join(x["w"] for x in cur + [w])
        gap = w["os"] - cur[-1]["oe"] if cur else 0
        if cur and (len(cur) >= max_words or len(text) > max_chars or gap > max_gap):
            groups.append(cur)
            cur = []
        cur.append(w)
        if w["w"][-1:] in ".?!,:;":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def _display(word: str, preset: dict, replacements: dict) -> str:
    w = replacements.get(word, replacements.get(tl.norm(word), word))
    w = w.strip()
    if preset.get("uppercase"):
        w = w.upper()
        w = w.rstrip(",.;:")
    return w


def caption_events(words: list[dict], cap: dict, preset: dict) -> list[str]:
    repl = cap.get("replacements", {}) or {}
    keys = {tl.norm(k) for k in cap.get("highlight_words", []) or []}
    y = preset.get("y", 1250)
    active = inline_color(preset.get("active_color", "#FFD400"))
    keyc = inline_color(preset.get("keyword_color", "#00E676"))
    base = inline_color(preset.get("color", "#FFFFFF"))
    groups = group_words(words, preset.get("max_words", 3), preset.get("max_chars", 18))
    events = []
    for gi, g in enumerate(groups):
        g_start = g[0]["os"]
        nxt = groups[gi + 1][0]["os"] if gi + 1 < len(groups) else g[-1]["oe"] + 0.4
        g_end = min(max(g[-1]["oe"], g_start + 0.25), nxt)
        disp = [_display(w["w"], preset, repl) for w in g]
        mode = preset.get("mode", "word")
        pos = f"\\an5\\pos({W // 2},{y})"
        if mode == "phrase":
            parts = []
            for w, d in zip(g, disp):
                parts.append(f"{{\\c{keyc}}}{esc(d)}{{\\c{base}}}" if tl.norm(w["w"]) in keys else esc(d))
            events.append(f"Dialogue: 0,{ts(g_start)},{ts(g_end)},Caption,,0,0,0,,{{{pos}\\fad(80,60)}}" + " ".join(parts))
            continue
        for k, w in enumerate(g):
            a = w["os"] if k else g_start
            b = g[k + 1]["os"] if k + 1 < len(g) else g_end
            if b - a < 0.02:
                continue
            parts = []
            for j, (ww, d) in enumerate(zip(g, disp)):
                is_key = tl.norm(ww["w"]) in keys
                if j == k:
                    col = keyc if is_key else active
                    grow = "\\fscx108\\fscy108" if mode == "word" else ""
                    parts.append(f"{{\\c{col}{grow}}}{esc(d)}{{\\c{base}\\fscx100\\fscy100}}")
                elif mode == "pop" and j > k:
                    parts.append(f"{{\\alpha&HFF&}}{esc(d)}{{\\alpha&H00&}}")  # parole future invisibili
                else:
                    parts.append(f"{{\\c{keyc}}}{esc(d)}{{\\c{base}}}" if is_key else esc(d))
            anim = ""
            if k == 0 and mode in ("pop", "word"):
                anim = "\\fscx70\\fscy70\\t(0,90,\\fscx112\\fscy112)\\t(90,160,\\fscx100\\fscy100)"
            line = " ".join(parts)
            events.append(f"Dialogue: 0,{ts(a)},{ts(b)},Caption,,0,0,0,,{{{pos}{anim}}}{line}")
    return events


def text_events(texts: list[dict], resolved: list[tuple[float, float]], styles: dict) -> list[str]:
    events = []
    for t, (a, b) in zip(texts, resolved):
        st = styles.get(t.get("style", "hook"), styles.get("hook", {}))
        txt = t["text"].upper() if st.get("uppercase") else t["text"]
        y = t.get("y", st.get("y", 520))
        x = t.get("x", W // 2)
        anim = t.get("anim", st.get("anim", "pop"))
        tag = f"\\an5\\pos({x},{y})"
        if anim == "pop":
            tag += "\\fscx40\\fscy40\\t(0,120,\\fscx115\\fscy115)\\t(120,200,\\fscx100\\fscy100)\\fad(0,120)"
        elif anim == "slide":
            tag = f"\\an5\\move({x},{y + 120},{x},{y},0,180)\\fad(120,120)"
        elif anim == "typewriter":
            n = max(1, len(txt))
            step = min(60, int(1000 * (b - a) * 0.5 / n))
            out, acc = [], 0
            for ch in txt:
                out.append(f"{{\\alpha&HFF&\\t({acc},{acc + 1},\\alpha&H00&)}}{esc(ch)}")
                acc += step
            events.append(f"Dialogue: 1,{ts(a)},{ts(b)},T_{t.get('style', 'hook')},,0,0,0,,{{{tag}}}" + "".join(out))
            continue
        else:
            tag += "\\fad(150,150)"
        events.append(f"Dialogue: 1,{ts(a)},{ts(b)},T_{t.get('style', 'hook')},,0,0,0,,{{{tag}}}{esc(txt)}")
    return events


def build(edl: dict, words_out: list[dict], text_times: list[tuple[float, float]]) -> str:
    presets = config.caption_presets()
    brand = config.brand()
    cap = edl.get("captions", {})
    preset = presets.get(cap.get("preset", "bold"), presets["bold"])
    preset = {**preset, **(cap.get("overrides") or {})}
    styles = [style_line("Caption", preset["font"], preset["size"], preset["color"], preset.get("outline_color", "#000000"),
                         preset.get("outline", 6), preset.get("shadow", 0), preset.get("box", False),
                         preset.get("box_color", "#000000"), preset.get("box_alpha", 0.5))]
    tstyles = brand.get("text_styles", {})
    for name, st in tstyles.items():
        styles.append(style_line(f"T_{name}", st.get("font", "Montserrat Black"), st.get("size", 80),
                                 st.get("color", "#FFFFFF"), st.get("outline_color", "#000000"),
                                 st.get("outline", 6), st.get("shadow", 0), st.get("box", False),
                                 st.get("box_color", "#000000"), st.get("box_alpha", 0.6)))
    header = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        *styles, "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events = []
    if cap.get("enabled", True) and words_out:
        events += caption_events(words_out, cap, preset)
    events += text_events(edl.get("texts", []), text_times, tstyles)
    return "\n".join(header + events) + "\n"
