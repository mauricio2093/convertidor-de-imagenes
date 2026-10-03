import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

import imgtool

SCRIPT = Path(imgtool.__file__)


def names(folder):
    return sorted(p.name for p in folder.iterdir())


def forbid_pool(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("no deberia crearse un pool de procesos")
    monkeypatch.setattr(imgtool, "ProcessPoolExecutor", boom)


# ----------------------------- formatos y transparencia -----------------------------

def test_rgba_png_to_jpeg_flattens_on_white(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png", mode="RGBA", color=(255, 0, 0, 0))
    assert imgtool.convert_images(src, out, "jpeg") == 0
    with Image.open(out / "a.jpeg") as img:
        assert img.mode == "RGB"
        assert all(c >= 250 for c in img.getpixel((10, 10)))


def test_palette_transparency_to_jpeg_flattens_on_white(dirs):
    src, out = dirs
    img = Image.new("P", (32, 32), 0)
    img.putpalette([0, 0, 0, 255, 0, 0])
    img.save(src / "p.png", transparency=0)
    assert imgtool.convert_images(src, out, "jpeg") == 0
    with Image.open(out / "p.jpeg") as result:
        assert all(c >= 250 for c in result.getpixel((5, 5)))


def test_la_png_to_jpeg(dirs, make_image):
    src, out = dirs
    make_image(src / "la.png", mode="LA", color=(0, 0))
    assert imgtool.convert_images(src, out, "jpeg") == 0
    with Image.open(out / "la.jpeg") as img:
        assert all(c >= 250 for c in img.getpixel((5, 5)))


@pytest.mark.parametrize("fmt", ["webp", "avif", "png"])
def test_alpha_is_kept_when_format_supports_it(dirs, make_image, fmt):
    src, out = dirs
    make_image(src / "a.bmp", mode="RGB")
    make_image(src / "t.tif", mode="RGBA", color=(0, 255, 0, 0))
    assert imgtool.convert_images(src, out, fmt) == 0
    with Image.open(out / f"t.{fmt}") as img:
        assert img.convert("RGBA").getpixel((5, 5))[3] == 0


def test_uppercase_extensions(dirs, make_image):
    src, out = dirs
    make_image(src / "A.PNG")
    make_image(src / "B.JPG")
    assert imgtool.convert_images(src, out, "webp") == 0
    assert names(out) == ["A.webp", "B.webp"]


def test_exif_orientation_is_applied(dirs):
    src, out = dirs
    img = Image.new("RGB", (60, 40), (10, 10, 200))
    exif = img.getexif()
    exif[0x0112] = 6
    img.save(src / "r.jpg", exif=exif)
    assert imgtool.convert_images(src, out, "webp") == 0
    with Image.open(out / "r.webp") as result:
        assert result.size == (40, 60)


@pytest.mark.parametrize("fmt", ["jpeg", "webp", "avif", "png"])
def test_icc_profile_is_preserved(dirs, fmt):
    from PIL import ImageCms
    src, out = dirs
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    Image.new("RGB", (32, 32), (9, 99, 199)).save(src / "c.tif", icc_profile=profile)
    assert imgtool.convert_images(src, out, fmt) == 0
    with Image.open(out / f"c.{fmt}") as img:
        assert img.info.get("icc_profile") == profile


def test_same_format_is_not_reconverted_with_any(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png")
    make_image(src / "b.webp")
    assert imgtool.convert_images(src, out, "webp") == 0
    assert names(out) == ["a.webp"]


# ----------------------------- nombres de salida -----------------------------

def test_name_collisions_get_distinct_outputs(dirs, make_image):
    src, out = dirs
    make_image(src / "foto.png")
    make_image(src / "foto.jpg")
    assert imgtool.convert_images(src, out, "webp") == 0
    assert names(out) == ["foto.webp", "foto_png.webp"]


def test_output_names_are_deterministic(tmp_path):
    files = [tmp_path / n for n in ("b.png", "a.jpg", "a.png", "a_png.jpg", "a.bmp")]
    ordered = sorted(files, key=imgtool._natural_key)
    plans = [imgtool.plan_outputs(ordered, tmp_path / "out", "webp") for _ in range(2)]
    assert plans[0] == plans[1]
    dests = [dest.name for _, dest in plans[0]]
    assert len(set(dests)) == len(files)
    assert dict((s.name, d.name) for s, d in plans[0])["a.bmp"] == "a.webp"


def test_collision_names_do_not_depend_on_skipped_files(dirs, make_image):
    src, out = dirs
    make_image(src / "foto.jpg")
    make_image(src / "foto.png")
    assert imgtool.convert_images(src, out, "webp") == 0
    first = {p.name: p.stat().st_mtime_ns for p in out.iterdir()}
    os.utime(src / "foto.png", ns=(2**62, max(first.values()) + 10**9))
    assert imgtool.convert_images(src, out, "webp") == 0
    after = {p.name: p.stat().st_mtime_ns for p in out.iterdir()}
    assert set(after) == set(first)
    assert after["foto.webp"] == first["foto.webp"]
    assert after["foto_png.webp"] != first["foto_png.webp"]


# ----------------------------- errores -----------------------------

def test_corrupt_file_does_not_abort_batch(dirs, make_image, capsys):
    src, out = dirs
    make_image(src / "a.png")
    (src / "b.png").write_text("no soy una imagen")
    make_image(src / "c.png")
    assert imgtool.convert_images(src, out, "jpeg") == 1
    assert names(out) == ["a.jpeg", "c.jpeg"]
    output = capsys.readouterr().out
    assert "ERROR  b.png" in output
    assert "Procesados: 2 | Omitidos: 0 | Fallidos: 1" in output


def test_failed_conversion_leaves_no_partial_file(dirs):
    src, out = dirs
    (src / "bad.png").write_text("x")
    assert imgtool.convert_images(src, out, "webp") == 1
    assert names(out) == []


def test_refuses_to_overwrite_its_own_input(dirs, make_image):
    src, _ = dirs
    make_image(src / "a.png")
    before = (src / "a.png").read_bytes()
    assert imgtool.convert_images(src, src, "png", "png") == 1
    assert (src / "a.png").read_bytes() == before


def test_empty_folder_is_not_an_error(dirs, capsys):
    src, out = dirs
    assert imgtool.convert_images(src, out, "webp") == 0
    assert "No hay archivos" in capsys.readouterr().out


# ----------------------------- incremental -----------------------------

def test_up_to_date_output_is_skipped(dirs, make_image, capsys):
    src, out = dirs
    make_image(src / "a.png")
    assert imgtool.convert_images(src, out, "webp") == 0
    stamp = (out / "a.webp").stat().st_mtime_ns
    capsys.readouterr()
    assert imgtool.convert_images(src, out, "webp") == 0
    assert (out / "a.webp").stat().st_mtime_ns == stamp
    assert "Procesados: 0 | Omitidos: 1 | Fallidos: 0" in capsys.readouterr().out


def test_force_reprocesses(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png")
    assert imgtool.convert_images(src, out, "webp", quality=90) == 0
    big = (out / "a.webp").read_bytes()
    make_image(src / "a.png", size=(128, 128))
    os.utime(src / "a.png", ns=(0, 0))  # origen "mas antiguo": sin --force se omitiria
    assert imgtool.convert_images(src, out, "webp") == 0
    assert (out / "a.webp").read_bytes() == big
    assert imgtool.convert_images(src, out, "webp", force=True) == 0
    with Image.open(out / "a.webp") as img:
        assert img.size == (128, 128)


def test_modified_source_is_reconverted(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png")
    assert imgtool.convert_images(src, out, "webp") == 0
    make_image(src / "a.png", size=(20, 20))
    newer = (out / "a.webp").stat().st_mtime_ns + 10**9
    os.utime(src / "a.png", ns=(newer, newer))
    assert imgtool.convert_images(src, out, "webp") == 0
    with Image.open(out / "a.webp") as img:
        assert img.size == (20, 20)


# ----------------------------- redimensionado -----------------------------

@pytest.mark.parametrize("fmt", ["jpeg", "webp", "avif", "png"])
def test_max_size_shrinks_longest_side(dirs, make_image, fmt):
    src, out = dirs
    make_image(src / "wide.bmp", size=(4000, 3000))
    make_image(src / "tall.tif", size=(1500, 3000))
    make_image(src / "pal.tif", size=(3000, 1000), mode="P", color=3)
    assert imgtool.convert_images(src, out, fmt, max_size=1920) == 0
    sizes = {}
    for p in out.iterdir():
        with Image.open(p) as img:
            sizes[p.stem] = img.size
    assert sizes == {"wide": (1920, 1440), "tall": (960, 1920), "pal": (1920, 640)}


def test_max_size_with_jpeg_source(dirs, make_image):
    src, out = dirs
    make_image(src / "foto.jpg", size=(4000, 3000))
    assert imgtool.convert_images(src, out, "webp", max_size=1000) == 0
    with Image.open(out / "foto.webp") as img:
        assert img.size == (1000, 750)


def test_max_size_never_enlarges(dirs, make_image):
    src, out = dirs
    make_image(src / "small.png", size=(800, 600))
    assert imgtool.convert_images(src, out, "webp", max_size=1920) == 0
    with Image.open(out / "small.webp") as img:
        assert img.size == (800, 600)


def test_no_resize_without_max_size(dirs, make_image):
    src, out = dirs
    make_image(src / "big.png", size=(2500, 500))
    assert imgtool.convert_images(src, out, "jpeg") == 0
    with Image.open(out / "big.jpeg") as img:
        assert img.size == (2500, 500)


# ----------------------------- AVIF -----------------------------

def test_avif_is_generated_and_readable(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png", size=(200, 100), color=(12, 180, 90))
    assert imgtool.convert_images(src, out, "avif") == 0
    with Image.open(out / "a.avif") as img:
        img.load()
        assert img.format == "AVIF"
        assert img.size == (200, 100)
        r, g, b = img.convert("RGB").getpixel((50, 50))
        assert abs(r - 12) < 12 and abs(g - 180) < 12 and abs(b - 90) < 12


def test_avif_as_source(dirs, make_image):
    src, out = dirs
    make_image(src / "a.avif")
    assert imgtool.convert_images(src, out, "jpeg") == 0
    assert names(out) == ["a.jpeg"]


def test_default_quality_depends_on_format():
    assert imgtool.encoder_args("avif")["quality"] == 60
    assert imgtool.encoder_args("jpeg")["quality"] == 85
    assert imgtool.encoder_args("webp")["quality"] == 85
    assert imgtool.encoder_args("webp", quality=40)["quality"] == 40
    assert "quality" not in imgtool.encoder_args("png")


# ----------------------------- paralelismo -----------------------------

def test_resolve_jobs():
    cpus = imgtool._cpu_count()
    assert imgtool.resolve_jobs(None, 0) == 1
    assert imgtool.resolve_jobs(8, 3) == 1            # pocos archivos: serie
    assert imgtool.resolve_jobs(1, 100) == 1          # --jobs 1 fuerza serie
    assert imgtool.resolve_jobs(None, 100) == min(cpus, imgtool.MAX_WORKERS)
    assert imgtool.resolve_jobs(10**6, 100) <= cpus   # sin sobresuscripcion
    assert imgtool.resolve_jobs(None, 4) <= 4         # nunca mas workers que archivos


def test_few_files_run_serially(dirs, make_image, monkeypatch):
    src, out = dirs
    for i in range(imgtool.SERIAL_THRESHOLD):
        make_image(src / f"{i}.png")
    forbid_pool(monkeypatch)
    assert imgtool.convert_images(src, out, "webp", jobs=8) == 0
    assert len(names(out)) == imgtool.SERIAL_THRESHOLD


def test_jobs_1_runs_serially(dirs, make_image, monkeypatch):
    src, out = dirs
    for i in range(8):
        make_image(src / f"{i}.png")
    forbid_pool(monkeypatch)
    assert imgtool.convert_images(src, out, "webp", jobs=1) == 0
    assert len(names(out)) == 8


@pytest.mark.parametrize("start_method", [None, "spawn"])
def test_parallel_matches_serial(tmp_path, make_image, monkeypatch, capsys, start_method):
    """'spawn' es el metodo que usa Windows."""
    src = tmp_path / "in"
    src.mkdir()
    for i in range(9):
        make_image(src / f"img{i}.png", color=(i * 20, 50, 200))
    (src / "img4b.png").write_text("corrupta")
    monkeypatch.setattr(imgtool, "START_METHOD", start_method)

    assert imgtool.convert_images(src, tmp_path / "par", "webp", jobs=2) == 1
    parallel_log = capsys.readouterr().out
    assert imgtool.convert_images(src, tmp_path / "ser", "webp", jobs=1) == 1
    serial_log = capsys.readouterr().out

    assert names(tmp_path / "par") == names(tmp_path / "ser") == [f"img{i}.webp" for i in range(9)]
    assert parallel_log == serial_log   # mismo orden y mismos mensajes
    for name in names(tmp_path / "par"):
        assert (tmp_path / "par" / name).read_bytes() == (tmp_path / "ser" / name).read_bytes()


# ----------------------------- CLI -----------------------------

def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_cli_parallel_end_to_end(dirs, make_image):
    src, out = dirs
    for i in range(6):
        make_image(src / f"{i}.png")
    (src / "x.png").write_text("corrupta")
    result = run_cli("convert", "--to", "avif", "--in", src, "--out", out, "--jobs", 2, "--max-size", 32)
    assert result.returncode == 1, result.stderr
    assert "Procesados: 6 | Omitidos: 0 | Fallidos: 1" in result.stdout
    assert names(out) == [f"{i}.avif" for i in range(6)]


def test_cli_compress(dirs, make_image):
    src, out = dirs
    make_image(src / "a.png")
    make_image(src / "b.jpg")
    result = run_cli("compress", "--in", src, "--out", out, "--level", 6)
    assert result.returncode == 0, result.stderr
    assert names(out) == ["a.png"]


@pytest.mark.parametrize("args", [
    ("--jobs", "0"), ("--jobs", "-2"), ("--jobs", "abc"),
    ("--max-size", "0"), ("--quality", "0"), ("--quality", "101"),
])
def test_cli_rejects_invalid_values(dirs, args):
    src, out = dirs
    result = run_cli("convert", "--to", "webp", "--in", src, "--out", out, *args)
    assert result.returncode == 2
    assert "debe ser un entero" in result.stderr


def test_cli_lossless_only_for_webp(dirs):
    src, out = dirs
    result = run_cli("convert", "--to", "jpeg", "--lossless", "--in", src, "--out", out)
    assert result.returncode == 2
    assert "--lossless" in result.stderr


def test_cli_missing_input_folder(tmp_path):
    result = run_cli("convert", "--to", "webp", "--in", tmp_path / "nope", "--out", tmp_path / "out")
    assert result.returncode == 1
    assert "No existe la carpeta" in result.stderr
