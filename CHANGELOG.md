# Changelog

Los cambios relevantes de este proyecto se documentan aqui.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa
[versionado semantico](https://semver.org/lang/es/).

## [2.1.0] - 2026-10-03

### Anadido
- Conversion en paralelo, con `--jobs N` para fijar el numero de procesos. Por defecto se usan
  todos los nucleos; con 3 archivos o menos se procesa en serie.
- Modo incremental: se omiten las imagenes cuyo destino ya existe y no es mas antiguo que el
  origen. `--force` reconvierte todo.
- `--max-size PX` para limitar el lado mas largo manteniendo la proporcion, sin agrandar nunca.
- Formato AVIF como destino (`--to avif`, calidad por defecto 60) y como origen.
- `--quality` se valida (1-100) y su valor por defecto depende del formato.
- Suite de tests con pytest (`tests/`, `requirements-dev.txt`).

### Cambiado
- El menu se reorganiza: accion, formato destino (JPEG, WebP, AVIF o PNG), origen, calidad,
  tamano maximo y si rehacer las ya convertidas. Las opciones de video pasan a ser la 3 y la 4.
- Se conserva el perfil de color ICC cuando el origen es RGB.
- Los nombres de salida ante colisiones (`foto.jpg` y `foto.png`) se asignan antes de convertir
  y ya no dependen de que el primer archivo se convierta bien.
- La salida se escribe en un archivo temporal y se renombra al terminar, de modo que una
  conversion interrumpida no deja un destino corrupto.
- El resumen final incluye el contador de omitidos.
- `--lossless` con un formato distinto de WebP es ahora un error en vez de ignorarse.
- Requisito minimo: Pillow 11.3 (por el soporte de AVIF).

### Corregido
- `compress --level` no tenia efecto: Pillow ignora el nivel cuando se pide optimizar, asi que
  siempre se usaba el 9. Ahora la optimizacion solo se activa en el nivel 9.
- `run.ps1` podia abortar al comprobar si Pillow estaba instalado en PowerShell 5.1.
- Ctrl+C durante un comando termina con el mensaje "Cancelado" y codigo de salida 130.

### Rendimiento medido
Lote de 40 imagenes de 3000-4000 px (20 PNG y 20 JPEG), en un Ryzen 7 5800H (8 nucleos, 16 hilos)
con WSL2. Mediana de 2-3 repeticiones; el peso de salida es identico al de 2.0.0.

| Operacion            | 2.0.0   | 2.1.0  | Mejora |
|----------------------|---------|--------|--------|
| PNG -> JPEG (20)     | 15,1 s  | 2,6 s  | 5,9x   |
| Todas -> WebP (40)   | 86,9 s  | 10,1 s | 8,6x   |
| Comprimir PNG (20)   | 165,5 s | 29,7 s | 5,6x   |

AVIF (nuevo): las mismas 40 imagenes pesan 13,4 MB frente a 18,8 MB en WebP (-29 %), pero tardan
25,2 s frente a 10,1 s. Con `--max-size 1920`: WebP 7,6 MB en 7,1 s y AVIF 4,6 MB en 12,3 s.

Se evaluaron y se descartaron como valores por defecto, por dar un ahorro minimo a cambio de mucho
mas tiempo de codificacion: WebP `method=6` (-0,6 % de peso, +60 % de tiempo) y JPEG progresivo
(-0,9 % de peso, +115 % de tiempo).

## [2.0.0] - 2026-10-01

### Cambiado
- Los seis scripts independientes (`converter.py`, `converter-v1.py`, `converterPngWebp.py`,
  `converterJpegWebp.py`, `changeName.py`, `changeName2.py`) se unifican en `imgtool.py`, con menu
  interactivo y los comandos `convert`, `compress`, `rename` y `clean`. **Cambio incompatible**:
  los scripts anteriores se eliminan.
- `release.ps1` y `release.sh` se sustituyen por los lanzadores `run.ps1` y `run.sh`, que crean el
  entorno virtual, instalan las dependencias y abren el menu.
- Las rutas son relativas al proyecto en lugar de rutas absolutas de Windows.
- PNG -> JPEG escribe en `imgOut` en lugar de `imgIn`.
- La numeracion de videos continua desde el numero mas alto de la carpeta de salida en lugar de
  un valor fijo en el codigo.

### Anadido
- Vista previa (`--dry-run`) para los comandos de video.
- `requirements.txt` y `.gitattributes` para normalizar los finales de linea.

### Corregido
- La transparencia quedaba en negro al convertir a JPEG; ahora se compone sobre blanco.
- Las extensiones en mayusculas (`.PNG`) se ignoraban en algunos scripts.
- Una imagen corrupta abortaba el lote completo.
- Los videos se ordenaban alfabeticamente (`10` antes que `2`), un nombre sin guion provocaba un
  error y podia sobrescribirse un archivo existente en destino.

## [1.0.0] - 2026-02-19

- Version inicial: scripts sueltos de conversion de imagenes y renombrado de videos.

[2.1.0]: https://github.com/mauricio2093/convertidor-de-imagenes/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/mauricio2093/convertidor-de-imagenes/releases/tag/v2.0.0
