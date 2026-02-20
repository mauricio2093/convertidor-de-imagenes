# imgePNGtoJPEG

Coleccion de scripts en Python para:
- convertir imagenes entre formatos (`PNG -> JPEG`, `PNG -> WEBP`, `JPEG -> WEBP`)
- comprimir PNG
- renombrar y mover archivos de video `.mp4`

El proyecto esta pensado para uso local y procesamiento por lotes usando carpetas de entrada/salida.

## Caracteristicas

- Conversion por lotes de imagenes.
- Compresion PNG con nivel configurable.
- Conversion con Pillow (`PIL`) para formatos web.
- Scripts separados para tareas especificas.
- Script de apoyo en PowerShell para activar entorno y analizar dependencias.

## Requisitos

- Python `3.12+` (el entorno actual fue creado con `3.12.5`)
- `pip`
- Libreria:
  - `Pillow`

Instalacion rapida:

```bash
python -m venv ENV
source ENV/bin/activate        # Linux/macOS
# o
ENV\Scripts\activate           # Windows (cmd)

pip install pillow
```

## Estructura del proyecto

```text
imgePNGtoJPEG/
├── converter.py
├── converter-v1.py
├── converterPngWebp.py
├── converterJpegWebp.py
├── changeName.py
├── changeName2.py
├── release.sh
├── release.ps1
├── imgIn/
├── imgOut/
├── videoIn/
├── videoOut/
└── videoOut2/
```

## Scripts principales

### 1) `converter.py`
- Convierte `PNG -> JPEG`.
- Usa `imgIn` como entrada y salida (sobrescritura por nuevo archivo `.jpeg` en la misma carpeta).

Ejecucion:

```bash
python converter.py
```

### 2) `converter-v1.py`
- Muestra dialogo (`tkinter`) para elegir:
  - comprimir `PNG -> PNG`
  - convertir `PNG -> JPEG`
- Entrada: `imgIn`
- Salida: `imgOut`

Ejecucion:

```bash
python converter-v1.py
```

### 3) `converterPngWebp.py`
- Convierte `PNG -> WEBP`.
- Entrada: `imgIn`
- Salida: `imgOut`

Ejecucion:

```bash
python converterPngWebp.py
```

### 4) `converterJpegWebp.py`
- Convierte `JPG/JPEG -> WEBP`.
- Entrada: `imgIn`
- Salida: `imgOut`

Ejecucion:

```bash
python converterJpegWebp.py
```

### 5) `changeName.py`
- Renombra y mueve videos `.mp4` con numeracion incremental.
- Entrada: `videoIn`
- Salida: `videoOut`

Ejecucion:

```bash
python changeName.py
```

### 6) `changeName2.py`
- Limpia prefijos en nombres de videos y normaliza formato.
- Entrada: `videoOut`
- Salida: `videoOut2`

Ejecucion:

```bash
python changeName2.py
```

## Nota importante sobre rutas

Los scripts usan rutas absolutas de Windows (por ejemplo `D:\programacion\python\imgePNGtoJPEG\...`).
Si clonas el repositorio en otra ubicacion, edita las variables de ruta al inicio de cada script.

## Publicacion en GitHub

Este repositorio incluye `.gitignore` para evitar subir:
- entorno virtual (`ENV/`)
- caches de Python
- archivos multimedia locales en carpetas de trabajo (`imgIn`, `imgOut`, `videoIn`, `videoOut`, `videoOut2`)

Flujo recomendado:

```bash
git init
git add .
git commit -m "feat: initial commit"
git branch -M main
git remote add origin <TU_REPO_URL>
git push -u origin main
```

## Licencia

Puedes agregar la licencia que prefieras (por ejemplo MIT) segun como quieras distribuir el proyecto.
