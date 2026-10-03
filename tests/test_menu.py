import pytest
from PIL import Image

import imgtool


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Redirige las carpetas de trabajo del menu a un directorio temporal."""
    folders = {}
    for attr in ("IMG_IN", "IMG_OUT", "VIDEO_IN", "VIDEO_OUT", "VIDEO_OUT2"):
        folders[attr] = tmp_path / attr.lower()
        monkeypatch.setattr(imgtool, attr, folders[attr])
    folders["IMG_IN"].mkdir()
    folders["VIDEO_IN"].mkdir()
    return folders


def answer(monkeypatch, *replies):
    replies = iter(replies)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))


def names(folder):
    return sorted(p.name for p in folder.iterdir())


def test_convert_to_avif_with_defaults(workspace, monkeypatch):
    Image.new("RGB", (300, 200)).save(workspace["IMG_IN"] / "a.png")
    Image.new("RGB", (300, 200)).save(workspace["IMG_IN"] / "b.jpg")
    # accion, formato AVIF, origen (Enter=todas), calidad (Enter), tamano (Enter=original), rehacer, salir
    answer(monkeypatch, "1", "3", "", "", "", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["IMG_OUT"]) == ["a.avif", "b.avif"]
    with Image.open(workspace["IMG_OUT"] / "a.avif") as img:
        assert img.size == (300, 200)


def test_convert_only_png_to_jpeg_with_max_size(workspace, monkeypatch):
    Image.new("RGB", (400, 200)).save(workspace["IMG_IN"] / "a.png")
    Image.new("RGB", (400, 200)).save(workspace["IMG_IN"] / "b.webp")
    answer(monkeypatch, "1", "1", "2", "70", "100", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["IMG_OUT"]) == ["a.jpeg"]
    with Image.open(workspace["IMG_OUT"] / "a.jpeg") as img:
        assert img.size == (100, 50)


def test_png_target_does_not_ask_for_quality(workspace, monkeypatch):
    Image.new("RGB", (40, 20)).save(workspace["IMG_IN"] / "a.jpg")
    # formato PNG, origen, tamano, rehacer (sin pregunta de calidad)
    answer(monkeypatch, "1", "4", "", "", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["IMG_OUT"]) == ["a.png"]


def test_webp_lossless_skips_quality(workspace, monkeypatch):
    Image.new("RGB", (40, 20), (1, 2, 3)).save(workspace["IMG_IN"] / "a.png")
    answer(monkeypatch, "1", "2", "", "s", "", "n", "0")
    assert imgtool.menu() == 0
    with Image.open(workspace["IMG_OUT"] / "a.webp") as img:
        assert img.convert("RGB").getpixel((5, 5)) == (1, 2, 3)


def test_invalid_answers_are_asked_again(workspace, monkeypatch, capsys):
    Image.new("RGB", (40, 20)).save(workspace["IMG_IN"] / "a.png")
    # opcion mala, formato malo, origen malo, calidad fuera de rango, tamano no numerico
    answer(monkeypatch, "9", "1", "7", "2", "x", "", "500", "80", "abc", "", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["IMG_OUT"]) == ["a.webp"]
    assert "Opcion no valida" in capsys.readouterr().out


def test_redo_question_forces_reconversion(workspace, monkeypatch, capsys):
    Image.new("RGB", (40, 20)).save(workspace["IMG_IN"] / "a.png")
    answer(monkeypatch, "1", "2", "", "n", "", "", "n", "1", "2", "", "n", "", "", "n", "1", "2", "", "n", "", "", "s", "0")
    assert imgtool.menu() == 0
    output = capsys.readouterr().out
    assert output.count("Procesados: 1 | Omitidos: 0") == 2
    assert output.count("Procesados: 0 | Omitidos: 1") == 1


def test_compress_png(workspace, monkeypatch):
    Image.new("RGB", (400, 100)).save(workspace["IMG_IN"] / "a.png")
    Image.new("RGB", (400, 100)).save(workspace["IMG_IN"] / "b.jpg")
    answer(monkeypatch, "2", "200", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["IMG_OUT"]) == ["a.png"]
    with Image.open(workspace["IMG_OUT"] / "a.png") as img:
        assert img.size == (200, 50)


def test_video_rename_asks_for_confirmation(workspace, monkeypatch):
    (workspace["VIDEO_IN"] / "clip.mp4").write_bytes(b"v")
    answer(monkeypatch, "3", "", "n", "0")
    assert imgtool.menu() == 0
    assert names(workspace["VIDEO_IN"]) == ["clip.mp4"]

    answer(monkeypatch, "3", "7", "s", "0")
    assert imgtool.menu() == 0
    assert names(workspace["VIDEO_OUT"]) == ["7- clip.mp4"]


def test_video_clean(workspace, monkeypatch):
    workspace["VIDEO_OUT"].mkdir()
    (workspace["VIDEO_OUT"] / "1- Y2meta.app - a.mp4").write_bytes(b"v")
    answer(monkeypatch, "4", "", "s", "0")
    assert imgtool.menu() == 0
    assert names(workspace["VIDEO_OUT2"]) == ["1- a.mp4"]


def test_single_ctrl_c_does_not_close_menu(workspace, monkeypatch, capsys):
    replies = iter([KeyboardInterrupt, "0"])

    def fake_input(prompt=""):
        reply = next(replies)
        if reply is KeyboardInterrupt:
            raise KeyboardInterrupt
        return reply
    monkeypatch.setattr("builtins.input", fake_input)
    assert imgtool.menu() == 0
    assert "Ctrl+C otra vez" in capsys.readouterr().out
