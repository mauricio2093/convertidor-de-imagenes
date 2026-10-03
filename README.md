# imgePNGtoJPEG

Herramienta en Python para procesar por lotes:
- convertir imagenes entre formatos (`JPEG`, `WebP`, `AVIF`, `PNG`)
- comprimir PNG
- redimensionar al convertir
- numerar, mover y limpiar nombres de videos `.mp4`

Todo vive en un solo script, `imgtool.py`, con menu interactivo y linea de comandos.
Las carpetas de trabajo son relativas al proyecto, asi que funciona igual en Windows, Linux y WSL.

## Instalacion y uso rapido

El lanzador crea el entorno virtual e instala las dependencias la primera vez:

```powershell
.\run.ps1                 # Windows: abre el menu
```

```bash
./run.sh                  # Linux / macOS / WSL / Git Bash: abre el menu
```

Instalacion manual, sin lanzador:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python imgtool.py
```

Requisitos: Python 3.10+ y Pillow. Para AVIF hace falta Pillow 11.3 o superior (no requiere nada mas).

## Menu

```text
 1) Convertir imagenes    (imgIn    -> imgOut)
 2) Comprimir PNG         (imgIn    -> imgOut)
 3) Numerar videos        (videoIn  -> videoOut)
 4) Limpiar nombres video (videoOut -> videoOut2)
 0) Salir
```

"Convertir imagenes" pregunta, en orden: formato destino (JPEG, WebP, AVIF o PNG), imagenes de
origen, calidad, tamano maximo (Enter = conservar la resolucion original) y si rehacer las que ya
estan convertidas. Las opciones de video muestran una vista previa y piden confirmacion antes de
mover nada.

## Linea de comandos

Cualquier argumento que pases al lanzador va directo a `imgtool.py`:

```bash
./run.sh convert --to webp --from png --quality 85
./run.sh convert --to avif --max-size 1920
./run.sh convert --to webp --lossless
./run.sh convert --to jpeg --in otra/carpeta --out otra/salida --jobs 4
./run.sh convert --to avif --quality 50 --force
./run.sh compress --level 9
./run.sh rename --start 92 --dry-run
./run.sh clean --prefix "Y2meta.app" --dry-run
```

| Comando    | Que hace                                               | Entrada / salida por defecto |
|------------|--------------------------------------------------------|------------------------------|
| `convert`  | Convierte a `jpeg`, `webp`, `avif` o `png`             | `imgIn` -> `imgOut`          |
| `compress` | Recomprime PNG sin cambiar de formato                  | `imgIn` -> `imgOut`          |
| `rename`   | Mueve los videos anteponiendo `N- ` (orden natural)    | `videoIn` -> `videoOut`      |
| `clean`    | Quita el prefijo de descarga y normaliza a `N- titulo` | `videoOut` -> `videoOut2`    |

Opciones de `convert` y `compress`:

| Opcion          | Efecto |
|-----------------|--------|
| `--to FORMATO`  | Formato destino (solo `convert`): `jpeg`, `webp`, `avif`, `png` |
| `--from ORIGEN` | Que archivos tomar (solo `convert`): `png`, `jpeg`, `webp`, `avif` o `any` (por defecto). Con `any` se leen PNG, JPG/JPEG, WebP, AVIF, BMP y TIFF, salvo los que ya estan en el formato destino |
| `--quality N`   | 1-100 (solo `convert`). Por defecto 85 en JPEG y WebP, y 60 en AVIF. No aplica a PNG |
| `--lossless`    | WebP sin perdida (solo con `--to webp`) |
| `--level 0-9`   | Nivel de compresion PNG (solo `compress`; por defecto 9) |
| `--max-size PX` | Limita el lado mas largo, manteniendo la proporcion. Nunca agranda. Sin la opcion no se redimensiona |
| `--jobs N`      | Procesos en paralelo. Por defecto, todos los nucleos |
| `--force`       | Reconvierte aunque el destino ya este actualizado |
| `--in`, `--out` | Carpetas de entrada y salida |

### Calidad y AVIF

La escala de calidad no es equivalente entre formatos: AVIF a 60 da una fidelidad similar a WebP
a 85 con archivos mas pequenos, a cambio de tardar mas en codificar. Por eso cada formato tiene su
propio valor por defecto.

### Procesamiento en paralelo

Las imagenes se convierten en varios procesos a la vez. `--jobs N` fija cuantos; nunca se usan mas
procesos que nucleos ni que archivos. Con 3 archivos o menos se procesa en serie, porque arrancar
procesos cuesta mas de lo que ahorra. `--jobs 1` fuerza el modo en serie.

### Modo incremental

Una imagen se omite si su destino ya existe y no es mas antiguo que el origen; el resumen final
indica cuantas se omitieron. Asi, repetir un lote solo procesa lo nuevo o lo modificado.

La comprobacion se basa unicamente en fechas de modificacion. Cambiar la calidad, el tamano maximo
u otras opciones **no** provoca la reconversion: usa `--force` (o responde "s" a "Rehacer" en el
menu) para regenerar con las opciones nuevas.

### Comportamiento con las imagenes

- Al convertir a JPEG, la transparencia se compone sobre fondo blanco (JPEG no la admite).
  WebP, AVIF y PNG la conservan.
- Se aplica la orientacion EXIF y se aceptan extensiones en mayusculas (`.PNG`, `.JPG`).
- El perfil de color ICC se conserva cuando el origen es RGB. El resto de metadatos EXIF
  (camara, GPS, fecha) no se copia a la salida.
- Si dos origenes darian el mismo nombre (`foto.jpg` y `foto.png`), el segundo se guarda como
  `foto_png.webp`. La asignacion es siempre la misma para la misma carpeta.
- Si un archivo falla, el lote continua; al final hay un resumen y el codigo de salida es `1`.

### Videos

- `rename` sin `--start` continua desde el numero mas alto que ya exista en la carpeta de salida.
- Los videos nunca sobrescriben un archivo existente en destino.

## Entorno virtual

- Windows usa `ENV/`; en Linux/WSL el lanzador usa `.venv/` (un venv de Windows no sirve en Linux).
- `.\run.ps1` deja el entorno activado en la consola al salir del menu. Para solo activarlo, sin menu: `.\run.ps1 -Activate`
- En bash, `source run.sh` deja el entorno activado; `source run.sh --activate` solo lo activa.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Las imagenes de prueba se generan al vuelo; no hay archivos binarios en el repositorio.

## Compatibilidad y limitaciones conocidas

- Desarrollado y probado en Linux (WSL2) con Python 3.13 y Pillow 12.3. En Windows el
  procesamiento en paralelo usa otro mecanismo de arranque de procesos; ese mecanismo esta
  cubierto por los tests en Linux, pero conviene probar `.\run.ps1` en tu equipo.
- Cada proceso carga una imagen completa en memoria. Con imagenes muy grandes y muchos nucleos,
  reduce `--jobs` si la memoria se queda corta.
- El modo incremental no detecta cambios de opciones (ver arriba) ni un origen modificado sin que
  cambie su fecha.
- De un GIF o WebP animado no se procesa la animacion; los GIF no se toman como origen.
- Al convertir a JPEG, WebP o AVIF, las imagenes en escala de grises o CMYK se pasan a RGB y no
  conservan su perfil de color.

## Estructura

```text
imgePNGtoJPEG/
├── imgtool.py              # toda la logica (menu + CLI)
├── run.ps1 / run.sh        # lanzadores
├── requirements.txt        # dependencias de uso
├── requirements-dev.txt    # dependencias para tests
├── tests/
├── CHANGELOG.md
├── imgIn/  imgOut/
└── videoIn/  videoOut/  videoOut2/
```

El contenido de las carpetas de trabajo y los entornos virtuales estan en `.gitignore`.
