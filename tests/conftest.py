import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# "Parlato" simulato: toni (voce) alternati a silenzi
SPEECH = [(0.0, 2.0), (3.2, 5.0), (5.3, 7.0), (9.0, 10.0)]
WORDS = [
    ("Ciao", 0.1, 0.5), ("a", 0.55, 0.65), ("tutti", 0.7, 1.2), ("oggi", 1.3, 1.9),
    ("ehm", 3.25, 3.7), ("vi", 3.8, 4.0), ("mostro", 4.05, 4.9),
    ("un", 5.35, 5.5), ("trucco", 5.55, 6.2), ("gratis", 6.3, 6.95),
    ("seguimi", 9.05, 9.9),
]


@pytest.fixture(scope="session", autouse=True)
def studio_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("studio")
    os.environ["REEL_STUDIO_DIR"] = str(d)
    return d


@pytest.fixture(scope="session")
def project(tmp_path_factory, studio_dir):
    from reel import config
    name = "_test_pytest"
    p = config.PROJECTS / name
    if p.exists():
        shutil.rmtree(p)
    (p / "raw").mkdir(parents=True)
    vol = "+".join(f"between(t,{a},{b})" for a, b in SPEECH)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30:d=10",
        "-f", "lavfi", "-i", "sine=f=220:d=10:sample_rate=48000",
        "-af", f"volume='0.5*({vol})':eval=frame",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(p / "raw" / "clip.mp4"),
    ], check=True)
    # musica finta per il test del ducking
    music = p / "music_test.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", "sine=f=440:d=4:sample_rate=48000", "-ac", "2", str(music)], check=True)
    from reel import project as prj
    prj.create(name)
    prj.ingest(p)
    words = [{"src": 0, "w": w, "s": s, "e": e, "p": 0.9} for w, s, e in WORDS]
    (p / "transcript.json").write_text(json.dumps({"language": "it", "words": words, "sentences": []}))
    yield p
    if not os.environ.get("REEL_KEEP_TEST"):
        shutil.rmtree(p, ignore_errors=True)
