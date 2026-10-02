"""Herramientas por lotes para imagenes (convertir/comprimir) y videos (numerar/limpiar nombres).

Sin argumentos abre un menu interactivo. Con argumentos:

    python imgtool.py convert --to webp --from png --quality 85
    python imgtool.py compress
    python imgtool.py rename --dry-run
    python imgtool.py clean --dry-run
"""
import argparse
import multiprocessing
import os
import re
import shutil
import signal
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
IMG_IN = BASE / "imgIn"
IMG_OUT = BASE / "imgOut"
VIDEO_IN = BASE / "videoIn"
VIDEO_OUT = BASE / "videoOut"
VIDEO_OUT2 = BASE / "videoOut2"

OUTPUT_EXT = {"jpeg": ".jpeg", "webp": ".webp", "avif": ".avif", "png": ".png"}
SOURCE_EXTS = {
    "png": {".png"},
    "jpeg": {".jpg", ".jpeg"},
    "webp": {".webp"},
    "avif": {".avif"},
    "any": {".png", ".jpg", ".jpeg", ".webp", ".avif", ".bmp", ".tif", ".tiff"},
}
# La escala de AVIF no equivale a la de JPEG/WEBP: 60 da una fidelidad comparable
DEFAULT_QUALITY = {"jpeg": 85, "webp": 85, "avif": 60}
DEFAULT_PREFIX = "Y2meta.app"
# Con tan pocos archivos, arrancar procesos cuesta mas de lo que ahorra
SERIAL_THRESHOLD = 3
MAX_WORKERS = 61  # limite de ProcessPoolExecutor en Windows
WEBP_METHOD = 4
# None = metodo predeterminado de la plataforma (spawn en Windows y macOS)
START_METHOD = None


# ----------------------------- utilidades -----------------------------

def _load_pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        sys.exit("Falta Pillow. Instala con: pip install -r requirements.txt")
    return Image, ImageOps


def _natural_key(path):
    """Orden natural: '2.mp4' va antes que '10.mp4'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path.name)]


def _list_files(folder, exts):
    if not folder.is_dir():
        sys.exit(f"No existe la carpeta de entrada: {folder}")
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(files, key=_natural_key)


def _fmt_size(num_bytes):
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / 1024:.0f} KB"


def _run_batch(files, action):
    """Ejecuta action(src) por archivo; un fallo no detiene el lote."""
    if not files:
        print("No hay archivos que procesar.")
        return 0
    failed = 0
    for src in files:
        try:
            print(f"  OK     {action(src)}")
        except Exception as e:
            failed += 1
            print(f"  ERROR  {src.name}: {e}")
    print(f"\nProcesados: {len(files) - failed} | Fallidos: {failed}")
    return 1 if failed else 0


# ----------------------------- imagenes -----------------------------

def _has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info


def _prepare(img, fmt, Image):
    """Deja la imagen en un modo valido para el formato de salida."""
    if fmt == "jpeg":
        if _has_alpha(img):
            # JPEG no tiene transparencia: componer sobre blanco (si no, queda negro)
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            return background
        return img.convert("RGB")
    if fmt in ("webp", "avif"):
        return img.convert("RGBA" if _has_alpha(img) else "RGB")
    if img.mode in ("CMYK", "YCbCr", "LAB", "HSV"):
        return img.convert("RGB")
    return img


def _shrink(img, max_size, Image):
    """Limita el lado mas largo a max_size manteniendo proporcion; nunca agranda."""
    if max(img.size) <= max_size:
        return img
    if img.mode in ("P", "1"):
        # Estos modos solo admiten vecino mas cercano; pasar a color real para reducir bien
        img = img.convert("RGBA" if _has_alpha(img) else "RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img


def _cpu_count():
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0)) or 1
    return os.cpu_count() or 1


def resolve_jobs(jobs, n_tasks):
    """Workers a usar: nunca mas que archivos ni que nucleos; lotes minimos van en serie."""
    if n_tasks <= SERIAL_THRESHOLD:
        return 1
    limit = min(_cpu_count(), MAX_WORKERS)
    return max(1, min(jobs or limit, limit, n_tasks))


def plan_outputs(files, out_dir, fmt):
    """Asigna a cada origen un destino unico, en orden, antes de convertir nada."""
    taken = set()
    plan = []
    for src in files:
        # p.ej. foto.jpg y foto.png -> foto.webp y foto_png.webp: no pisar el primero
        tagged = f"{src.stem}_{src.suffix.lstrip('.').lower()}"
        name, n = src.stem, 1
        while name.lower() in taken:
            name = tagged if n == 1 else f"{tagged}_{n}"
            n += 1
        taken.add(name.lower())
        plan.append((src, out_dir / (name + OUTPUT_EXT[fmt])))
    return plan


def is_up_to_date(src, dest):
    """El destino existe y no es mas antiguo que el origen."""
    try:
        return dest.stat().st_mtime >= src.stat().st_mtime
    except OSError:
        return False


def _convert_one(task):
    """Convierte un archivo; corre en un worker, asi que no decide nombres ni comparte estado."""
    src, dest, fmt, save_args, max_size = task
    try:
        from PIL import Image, ImageOps
        if dest.resolve() == src.resolve():
            raise ValueError("la salida pisaria el archivo de entrada (usa otra carpeta --out)")
        # Escribir a un temporal y renombrar: un fallo a medias no deja un destino
        # corrupto que luego se omitiria por "ya convertido"
        partial = dest.with_name(dest.name + ".part")
        try:
            with Image.open(src) as img:
                # El perfil de color solo sigue siendo valido si el origen ya era RGB
                icc = img.info.get("icc_profile") if img.mode in ("RGB", "RGBA", "P") else None
                if icc:
                    save_args = {**save_args, "icc_profile": icc}
                if max_size and img.format == "JPEG":
                    # Decodificar ya reducido (con margen x2 para no perder calidad)
                    img.draft(None, (max_size * 2, max_size * 2))
                img = _prepare(ImageOps.exif_transpose(img), fmt, Image)
                if max_size:
                    img = _shrink(img, max_size, Image)
                img.save(partial, fmt.upper(), **save_args)
            os.replace(partial, dest)
        finally:
            partial.unlink(missing_ok=True)
        before, after = src.stat().st_size, dest.stat().st_size
        change = (after - before) / before * 100 if before else 0
        return True, (f"{src.name} -> {dest.name}  "
                      f"({_fmt_size(before)} -> {_fmt_size(after)}, {change:+.0f}%)")
    except Exception as e:
        return False, f"{src.name}: {e}"


def _worker_init():
    # Ctrl+C lo gestiona el proceso principal; el worker termina su imagen en curso
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _run_tasks(tasks, jobs):
    """Genera (ok, mensaje) en el mismo orden que tasks."""
    if jobs == 1:
        yield from map(_convert_one, tasks)
        return
    pool = ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context(START_METHOD),
                               initializer=_worker_init)
    try:
        futures = [pool.submit(_convert_one, task) for task in tasks]
        for task, future in zip(tasks, futures):
            try:
                yield future.result()
            except Exception as e:
                # El worker murio (p.ej. sin memoria): cuenta como fallo de ese archivo
                yield False, f"{task[0].name}: {e or type(e).__name__}"
    finally:
        pool.shutdown(wait=True, cancel_futures=True)


def encoder_args(fmt, quality=None, lossless=False, compress_level=9):
    if fmt == "png":
        # Pillow ignora compress_level cuando optimize=True (fuerza el 9)
        return {"optimize": compress_level == 9, "compress_level": compress_level}
    args = {"quality": quality or DEFAULT_QUALITY[fmt]}
    if fmt == "jpeg":
        args.update(optimize=True)
    elif fmt == "webp":
        args.update(lossless=lossless, method=WEBP_METHOD)
    return args


def convert_images(in_dir, out_dir, fmt, source="any", quality=None,
                   lossless=False, compress_level=9, jobs=None, force=False, max_size=None):
    _load_pillow()
    exts = SOURCE_EXTS[source]
    if source == "any":
        # No reconvertir archivos que ya estan en el formato destino
        exts = exts - SOURCE_EXTS[fmt]
    files = _list_files(in_dir, exts)
    if not files:
        print("No hay archivos que procesar.")
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)

    save_args = encoder_args(fmt, quality, lossless, compress_level)
    plan = plan_outputs(files, out_dir, fmt)
    tasks = [(src, dest, fmt, save_args, max_size) for src, dest in plan
             if force or not is_up_to_date(src, dest)]
    skipped = len(plan) - len(tasks)
    failed = 0
    for ok, message in _run_tasks(tasks, resolve_jobs(jobs, len(tasks))):
        failed += not ok
        print(f"  {'OK   ' if ok else 'ERROR'}  {message}")
    print(f"\nProcesados: {len(tasks) - failed} | Omitidos: {skipped} | Fallidos: {failed}")
    if skipped:
        print("(omitidos: ya estaban convertidos; usa --force para rehacerlos)")
    return 1 if failed else 0


# ----------------------------- videos -----------------------------

def _next_start(out_dir, ext):
    """Siguiente numero libre segun los archivos ya numerados en out_dir."""
    highest = 0
    if out_dir.is_dir():
        for p in out_dir.iterdir():
            m = re.match(r"(\d+)\s*-", p.name)
            if m and p.suffix.lower() == ext:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def _move(src, dest, dry_run):
    if dest.exists():
        raise FileExistsError(f"ya existe {dest.name} en destino")
    if not dry_run:
        shutil.move(str(src), str(dest))
    return f"{src.name} -> {dest.name}"


def rename_videos(in_dir, out_dir, start=None, ext=".mp4", dry_run=False):
    """Mueve los videos a out_dir anteponiendo numeracion: 'N- nombre.mp4'."""
    files = _list_files(in_dir, {ext})
    if start is None:
        start = _next_start(out_dir, ext)
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    numbers = dict(zip(files, range(start, start + len(files))))
    return _run_batch(files, lambda src: _move(src, out_dir / f"{numbers[src]}- {src.name}", dry_run))


def clean_name(name, prefix=DEFAULT_PREFIX):
    """Quita el prefijo de descarga y normaliza a 'N- titulo'."""
    name = re.sub(re.escape(prefix) + r"\s*-\s*", "", name, flags=re.IGNORECASE)
    m = re.match(r"(\d+)\s*-\s*(.+)$", name)
    return f"{m.group(1)}- {m.group(2)}" if m else name.strip()


def clean_videos(in_dir, out_dir, prefix=DEFAULT_PREFIX, ext=".mp4", dry_run=False):
    files = _list_files(in_dir, {ext})
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    return _run_batch(files, lambda src: _move(src, out_dir / clean_name(src.name, prefix), dry_run))


# ----------------------------- menu -----------------------------

MENU = """
========== imgtool ==========
 1) PNG -> JPEG
 2) PNG -> WEBP
 3) JPG/JPEG -> WEBP
 4) Cualquier imagen -> WEBP
 5) Comprimir PNG (PNG -> PNG)
 6) Numerar videos        (videoIn  -> videoOut)
 7) Limpiar nombres video (videoOut -> videoOut2)
 0) Salir
"""


def _ask_int(prompt, default, low, high):
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and low <= int(raw) <= high:
            return int(raw)
        print(f"  Escribe un numero entre {low} y {high}.")


def _ask_yes(prompt):
    return input(f"{prompt} (s/N): ").strip().lower() in ("s", "si", "sí")


def _preview_then_apply(func, *args):
    print("\nVista previa (no se mueve nada todavia):")
    if func(*args, dry_run=True) == 0 and _ask_yes("¿Aplicar estos cambios?"):
        func(*args, dry_run=False)


def menu():
    interrupted = False
    while True:
        print(MENU)
        try:
            choice = input("Elige una opcion: ").strip()
        except KeyboardInterrupt:
            # Un solo Ctrl+C no cierra: VS Code lo envia al auto-activar el venv en la terminal
            if interrupted:
                raise
            interrupted = True
            print("\n(Ctrl+C otra vez, o 0, para salir)")
            continue
        interrupted = False
        print()
        if choice == "0":
            return 0
        if choice == "1":
            convert_images(IMG_IN, IMG_OUT, "jpeg", "png", _ask_int("Calidad (1-100)", DEFAULT_QUALITY["jpeg"], 1, 100))
        elif choice in ("2", "3", "4"):
            source = {"2": "png", "3": "jpeg", "4": "any"}[choice]
            lossless = _ask_yes("¿Sin perdida (lossless)?")
            quality = None if lossless else _ask_int("Calidad (1-100)", DEFAULT_QUALITY["webp"], 1, 100)
            convert_images(IMG_IN, IMG_OUT, "webp", source, quality, lossless)
        elif choice == "5":
            convert_images(IMG_IN, IMG_OUT, "png", "png")
        elif choice == "6":
            start = _ask_int("Numero inicial", _next_start(VIDEO_OUT, ".mp4"), 0, 10**6)
            _preview_then_apply(rename_videos, VIDEO_IN, VIDEO_OUT, start, ".mp4")
        elif choice == "7":
            prefix = input(f"Prefijo a quitar [{DEFAULT_PREFIX}]: ").strip() or DEFAULT_PREFIX
            _preview_then_apply(clean_videos, VIDEO_OUT, VIDEO_OUT2, prefix, ".mp4")
        else:
            print("Opcion no valida.")


# ----------------------------- CLI -----------------------------

def _ext(value):
    return "." + value.lower().lstrip(".")


def _quality(value):
    if not value.isdigit() or not 1 <= int(value) <= 100:
        raise argparse.ArgumentTypeError(f"debe ser un entero entre 1 y 100 (recibido: {value!r})")
    return int(value)


def _positive_int(value):
    if not value.isdigit() or int(value) < 1:
        raise argparse.ArgumentTypeError(f"debe ser un entero mayor o igual a 1 (recibido: {value!r})")
    return int(value)


def build_parser():
    parser = argparse.ArgumentParser(description="Herramientas por lotes para imagenes y videos.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("convert", help="Convertir imagenes a JPEG, WEBP, AVIF o PNG")
    p.add_argument("--to", dest="fmt", choices=sorted(OUTPUT_EXT), required=True)
    p.add_argument("--from", dest="source", choices=sorted(SOURCE_EXTS), default="any")
    p.add_argument("--quality", type=_quality,
                   help="1-100; por defecto 85 en JPEG/WEBP y 60 en AVIF (no aplica a PNG)")
    p.add_argument("--lossless", action="store_true", help="WEBP sin perdida")
    p.add_argument("--in", dest="in_dir", type=Path, default=IMG_IN)
    p.add_argument("--out", dest="out_dir", type=Path, default=IMG_OUT)

    p = sub.add_parser("compress", help="Comprimir PNG sin cambiar de formato")
    p.add_argument("--level", type=int, default=9, choices=range(10), metavar="0-9")
    p.add_argument("--in", dest="in_dir", type=Path, default=IMG_IN)
    p.add_argument("--out", dest="out_dir", type=Path, default=IMG_OUT)

    p = sub.add_parser("rename", help="Numerar y mover videos")
    p.add_argument("--start", type=int, help="Numero inicial (por defecto: el siguiente libre en --out)")
    p.add_argument("--in", dest="in_dir", type=Path, default=VIDEO_IN)
    p.add_argument("--out", dest="out_dir", type=Path, default=VIDEO_OUT)

    p = sub.add_parser("clean", help="Quitar prefijo de descarga y normalizar nombres de video")
    p.add_argument("--prefix", default=DEFAULT_PREFIX)
    p.add_argument("--in", dest="in_dir", type=Path, default=VIDEO_OUT)
    p.add_argument("--out", dest="out_dir", type=Path, default=VIDEO_OUT2)

    for name in ("convert", "compress"):
        sub.choices[name].add_argument("--jobs", type=_positive_int, metavar="N",
                                       help="Procesos en paralelo (por defecto: todos los nucleos)")
        sub.choices[name].add_argument("--max-size", type=_positive_int, metavar="PX",
                                       help="Lado mas largo maximo en pixeles (nunca agranda)")
        sub.choices[name].add_argument("--force", action="store_true",
                                       help="Reconvertir aunque el destino ya este actualizado")
    for name in ("rename", "clean"):
        sub.choices[name].add_argument("--ext", type=_ext, default=".mp4")
        sub.choices[name].add_argument("--dry-run", action="store_true", help="Mostrar sin mover nada")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "convert" and args.lossless and args.fmt != "webp":
        parser.error("--lossless solo aplica a --to webp")
    if args.command is None:
        try:
            return menu()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
    if args.command == "convert":
        return convert_images(args.in_dir, args.out_dir, args.fmt, args.source, args.quality, args.lossless,
                              jobs=args.jobs, force=args.force, max_size=args.max_size)
    if args.command == "compress":
        return convert_images(args.in_dir, args.out_dir, "png", "png", compress_level=args.level,
                              jobs=args.jobs, force=args.force, max_size=args.max_size)
    if args.command == "rename":
        return rename_videos(args.in_dir, args.out_dir, args.start, args.ext, args.dry_run)
    return clean_videos(args.in_dir, args.out_dir, args.prefix, args.ext, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
