"""Flusso 'facile': video trascinato nella cartella del Desktop -> progetto -> video pronto."""
import shutil
import subprocess

from reel import cli, config, ff


def test_inbox_to_project_with_hdr_iphone_clip(studio_dir):
    inbox = config.inbox()
    inbox.mkdir(parents=True, exist_ok=True)
    clip = inbox / "IMG_0001.MOV"
    # clip "tipo iPhone": verticale, 10 bit, etichettata HDR HLG
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=360x640:r=30:d=2",
                    "-f", "lavfi", "-i", "sine=f=300:d=2", "-c:v", "libx264", "-profile:v", "high10",
                    "-pix_fmt", "yuv420p10le", "-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
                    "-colorspace", "bt2020nc", "-c:a", "aac", "-shortest", str(clip)], check=True)
    assert ff.probe(clip)["hdr"]
    name = "_test_inbox"
    p = config.PROJECTS / name
    shutil.rmtree(p, ignore_errors=True)
    try:
        cli.main(["new", name, "--from-inbox"])
        assert not clip.exists() and (p / "raw" / "IMG_0001.MOV").exists()
        src = p / "work" / "IMG_0001_norm.mp4"
        info = ff.probe(src)
        assert not info["hdr"] and info["pix_fmt"] == "yuv420p"
        cli.main(["captions", name, "--off"])
        cli.main(["render", name])
        assert (config.outbox() / f"{name}.mp4").exists()
    finally:
        shutil.rmtree(p, ignore_errors=True)
