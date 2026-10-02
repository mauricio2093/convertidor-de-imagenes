# imgePNGtoJPEG

Herramienta en Python para procesar por lotes:
- convertir imagenes entre formatos (`PNG`, `JPEG`, `WEBP`)
- comprimir PNG
- numerar, mover y limpiar nombres de videos `.mp4`

Todo vive en un solo script, `imgtool.py`, con menu interactivo y linea de comandos.
Las carpetas de trabajo son relativas al proyecto, asi que funciona igual en Windows, Linux y WSL.

## Uso rapido

El lanzador crea el entorno virtual e instala las dependencias la primera vez:

```powershell
.\run.ps1                 # Windows: abre el menu
```

```bash
./run.sh                  # Linux / macOS / WSL: abre el menu
```

Menu:

```text
 1) PNG -> JPEG
 2) PNG -> WEBP
 3) JPG/JPEG -> WEBP
 4) Cualquier imagen -> WEBP
 5) Comprimir PNG (PNG -> PNG)
 6) Numerar videos        (videoIn  -> videoOut)
 7) Limpiar nombres video (videoOut -> videoOut2)
 0) Salir
```

Las opciones de video muestran una vista previa y piden confirmacion antes de mover nada.

## Linea de comandos

Cualquier argumento que pases al lanzador va directo a `imgtool.py`:

```bash
./run.sh convert --to webp --from png --quality 85
./run.sh convert --to webp --lossless
./run.sh convert --to jpeg --in otra/carpeta --out otra/salida
./run.sh compress --level 9
./run.sh rename --start 92 --dry-run
./run.sh clean --prefix "Y2meta.app" --dry-run
```

| Comando    | Que hace                                              | Entrada / salida por defecto |
|------------|-------------------------------------------------------|------------------------------|
| `convert`  | Convierte a `jpeg`, `webp` o `png` (`--from png|jpeg|webp|any`) | `imgIn` -> `imgOut` |
| `compress` | Recomprime PNG sin cambiar de formato                 | `imgIn` -> `imgOut`          |
| `rename`   | Mueve los videos anteponiendo `N- ` (orden natural)   | `videoIn` -> `videoOut`      |
| `clean`    | Quita el prefijo de descarga y normaliza a `N- titulo`| `videoOut` -> `videoOut2`    |

Detalles:
- Al convertir a JPEG, la transparencia se compone sobre fondo blanco.
- Se respeta la orientacion EXIF y las extensiones en mayusculas (`.PNG`, `.JPG`).
- Si un archivo falla, el lote continua; al final hay un resumen y el codigo de salida es `1`.
- `rename` sin `--start` continua desde el numero mas alto que ya exista en la carpeta de salida.
- Los videos nunca sobrescriben un archivo existente en destino.

## Entorno virtual

- Windows usa `ENV/`; en Linux/WSL el lanzador usa `.venv/` (un venv de Windows no sirve en Linux).
- `.\run.ps1` deja el entorno activado en la consola al salir del menu. Para solo activarlo, sin menu: `.\run.ps1 -Activate`
- Instalacion manual: `python -m venv ENV` y `pip install -r requirements.txt`

Requisitos: Python 3.10+ y `Pillow`.

## Estructura

```text
imgePNGtoJPEG/
├── imgtool.py          # toda la logica (menu + CLI)
├── run.ps1 / run.sh    # lanzadores
├── requirements.txt
├── imgIn/  imgOut/
└── videoIn/  videoOut/  videoOut2/
```

El contenido de las carpetas de trabajo y los entornos virtuales estan en `.gitignore`.
