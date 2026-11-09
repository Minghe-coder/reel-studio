"""Test end-to-end su un video sintetico (orizzontale 1920x1080 -> verticale 1080x1920)."""
from reel import cli, edl as E, ff
from reel import timeline as tl


def run(*args):
    cli.main([str(a) for a in args])


def test_autocut_removes_silences_and_fillers(project):
    run("autocut", project, "--level", "normale")
    edl = E.load(project)
    total = tl.total_duration(edl["segments"])
    assert 5.5 < total < 8.0, total          # 10 s -> ~7 s (via silenzi lunghi + "ehm")
    # il silenzio 7-9 s non deve esserci
    assert all(not (s["in"] < 8.0 < s["out"]) for s in edl["segments"])
    # "ehm" (3.25-3.7) rimosso
    assert all(not (s["in"] < 3.5 < s["out"]) for s in edl["segments"])


def test_edit_commands(project):
    run("autozoom", project, "--max-len", "1.5")
    run("captions", project, "--preset", "bold", "--highlight", "gratis")
    run("text", project, "3 trucchi gratis", "--at", "0", "--dur", "2", "--style", "hook")
    run("text", project, "Seguimi!", "--at", "parola:seguimi", "--end", "-0", "--style", "cta", "--anim", "slide")
    run("sfx", project, "sfx/boom/boom_1.wav", "--at", "0")
    run("transition", project, "--type", "flash", "--all-cuts", "--sfx", "sfx/whoosh/whoosh_2.wav")
    run("music", project, str(project / "music_test.wav"), "--volume", "0.2")
    run("progress", project, "on")
    edl = E.load(project)
    assert edl["captions"]["highlight_words"] == ["gratis"]
    assert len(edl["texts"]) == 2 and edl["texts"][1]["start"] == {"word": "seguimi", "n": 1}
    assert any(s["zoom"] != 1.0 for s in edl["segments"])


def test_popup_with_generated_image(project):
    img = project / "arrow.png"
    ff.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red@1:s=200x200:d=1,format=rgba",
            "-frames:v", "1", str(img)])
    run("popup", project, "--image", img, "--at", "parola:gratis", "--dur", "1.2", "--sfx", "sfx/pop/pop_1.wav")
    assert len(E.load(project)["popups"]) == 1


def test_render_final_meets_specs(project):
    run("render", project)
    out = project / "out" / "final.mp4"
    info = ff.probe(out)
    assert (info["width"], info["height"]) == (1080, 1920)
    assert abs(info["fps"] - 30) < 0.1
    assert info["vcodec"] == "h264" and info["acodec"] == "aac"
    total = tl.total_duration(E.load(project)["segments"])
    assert abs(info["duration"] - total) < 0.15
    loud = ff.measure_loudness(out)
    assert abs(loud["integrated"] - (-14)) <= 1.5, loud
    ass = (project / "out" / "captions.ass").read_text(encoding="utf-8")
    assert "GRATIS" in ass and "SEGUIMI!" in ass
    cta = [l for l in ass.splitlines() if "SEGUIMI!" in l][0]
    assert cta.split(",")[2] == "0:00:06.60"  # la CTA resta fino alla fine
    assert (project / "out" / "qc" / "frame_1.jpg").exists()


def test_preview_and_undo(project):
    run("preview", project)
    assert ff.probe(project / "out" / "preview.mp4")["width"] == 540
    before = len(E.load(project)["popups"])
    run("undo", project)  # annulla l'ultima modifica (popup)
    assert len(E.load(project)["popups"]) == before - 1
