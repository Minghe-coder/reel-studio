from reel import timeline as tl

SEGS = [{"src": 0, "in": 0.0, "out": 2.0}, {"src": 0, "in": 3.0, "out": 5.0}, {"src": 1, "in": 1.0, "out": 2.0}]


def test_offsets_and_mapping():
    assert tl.offsets(SEGS) == [0.0, 2.0, 4.0]
    assert tl.total_duration(SEGS) == 5.0
    assert tl.src_to_out(SEGS, 0, 3.5) == 2.5
    assert tl.src_to_out(SEGS, 0, 2.5) is None
    assert tl.out_to_src(SEGS, 4.5) == (2, 1, 1.5)


def test_cut_out_and_zoom():
    segs = tl.cut_out(SEGS, 1.0, 3.0)
    assert abs(tl.total_duration(segs) - 3.0) < 1e-6
    z = tl.set_zoom(SEGS, 0.5, 1.5, 1.3)
    assert [round(s["out"] - s["in"], 2) for s in z[:3]] == [0.5, 1.0, 0.5]
    assert z[1]["zoom"] == 1.3


def test_remove_src_range_and_move():
    segs = tl.remove_src_range(SEGS, 0, 3.5, 4.0)
    assert len(segs) == 4
    moved = tl.move_block(SEGS, 4.0, 5.0, 0.0)
    assert moved[0]["src"] == 1


def test_find_phrase_and_anchor():
    words = [{"src": 0, "w": "Ciao,", "s": 0.1, "e": 0.4}, {"src": 0, "w": "è", "s": 0.5, "e": 0.6},
             {"src": 0, "w": "Gratis!", "s": 3.2, "e": 3.8}]
    assert tl.find_phrase(words, "ciao e") == [(0, 1)]
    assert abs(tl.resolve({"word": "gratis"}, SEGS, words) - 2.2) < 1e-6
    assert tl.resolve(-1, SEGS, words) == 4.0
    assert tl.parse_time("1:02,5") == 62.5


def test_fix_word_ends_clips_into_silence():
    from reel.transcribe import fix_word_ends
    words = [{"src": 0, "w": "ciao", "s": 1.0, "e": 2.5}]
    fix_word_ends(words, {0: [(1.6, 3.0)]})
    assert words[0]["e"] == 1.6


def test_captions_grouping_and_colors():
    from reel import captions_ass
    assert captions_ass.ass_color("#FFD400") == "&H0000D4FF"
    ws = [{"w": w, "os": i * 0.3, "oe": i * 0.3 + 0.25} for i, w in enumerate("uno due tre quattro. cinque".split())]
    groups = captions_ass.group_words(ws, 3, 18)
    assert [len(g) for g in groups] == [3, 1, 1]
