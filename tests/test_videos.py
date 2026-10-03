import imgtool


def touch(folder, *names):
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_bytes(b"video")


def names(folder):
    return sorted(p.name for p in folder.iterdir())


def test_rename_uses_natural_order(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    touch(src, "clip10.mp4", "clip2.mp4", "clip1.mp4", "notas.txt")
    assert imgtool.rename_videos(src, out, start=5) == 0
    assert names(out) == ["5- clip1.mp4", "6- clip2.mp4", "7- clip10.mp4"]
    assert names(src) == ["notas.txt"]


def test_rename_continues_from_highest_number(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    touch(src, "nuevo.mp4")
    touch(out, "3- a.mp4", "12- b.mp4")
    assert imgtool.rename_videos(src, out) == 0
    assert "13- nuevo.mp4" in names(out)


def test_rename_dry_run_moves_nothing(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    touch(src, "a.mp4")
    assert imgtool.rename_videos(src, out, start=1, dry_run=True) == 0
    assert names(src) == ["a.mp4"]
    assert not out.exists()


def test_rename_never_overwrites_destination(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    touch(src, "a.mp4")
    out.mkdir()
    (out / "1- a.mp4").write_bytes(b"original")
    assert imgtool.rename_videos(src, out, start=1) == 1
    assert (out / "1- a.mp4").read_bytes() == b"original"
    assert names(src) == ["a.mp4"]


def test_clean_name():
    assert imgtool.clean_name("92- Y2meta.app - Titulo.mp4") == "92- Titulo.mp4"
    assert imgtool.clean_name("7 -Y2meta.app-Otro - tema.mp4") == "7- Otro - tema.mp4"
    assert imgtool.clean_name("sin guion.mp4") == "sin guion.mp4"
    assert imgtool.clean_name("3- X - a.mp4", prefix="X") == "3- a.mp4"


def test_clean_moves_and_never_overwrites(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    touch(src, "1- Y2meta.app - a.mp4", "2- Y2meta.app - b.mp4")
    out.mkdir()
    (out / "2- b.mp4").write_bytes(b"original")
    assert imgtool.clean_videos(src, out) == 1
    assert names(out) == ["1- a.mp4", "2- b.mp4"]
    assert (out / "2- b.mp4").read_bytes() == b"original"
    assert names(src) == ["2- Y2meta.app - b.mp4"]
