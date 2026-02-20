# Activador y analizador seguro de entorno virtual para Python (PowerShell)
param(
    [string]$venvName = "ENV",
    [switch]$analyze
)

$ErrorActionPreference = "Stop"

# -----------------------------
# 1) Activar entorno virtual
# -----------------------------
$venvPath = Join-Path $PSScriptRoot $venvName
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-Not (Test-Path $activateScript)) {
    Write-Host "No se encontro el entorno virtual en: $venvPath" -ForegroundColor Red
    Write-Host "Crea el venv con: python -m venv $venvName" -ForegroundColor Yellow
    exit 1
}

Write-Host "Activando entorno virtual ($venvName)..." -ForegroundColor Green
. $activateScript

Write-Host "Python: " -NoNewline; python --version
Write-Host "Pip:    " -NoNewline; pip --version

# Si solo quieres activar, termina aquí (por defecto)
if (-not $analyze) {
    Write-Host "`nEntorno activado. (Tip: ejecuta `. .\release.ps1 -analyze` para analizar dependencias)" -ForegroundColor Cyan
    exit 0
}

# -----------------------------
# 2) Analizar dependencias (solo proyecto)
# -----------------------------
Write-Host "`nAnalizando dependencias del proyecto (solo tu codigo)..." -ForegroundColor Cyan

# Carpetas a excluir del análisis
$excludeDirs = @(
  $venvName, ".venv", "venv",
  "__pycache__", ".git",
  "build", "dist",
  ".pytest_cache", ".mypy_cache",
  ".tox", ".ruff_cache",
  "node_modules"
)

# Obtener .py excluyendo carpetas
$pyFiles = Get-ChildItem -Path $PSScriptRoot -Recurse -Filter *.py -File |
  Where-Object {
    $full = $_.FullName
    -not ($excludeDirs | ForEach-Object { $full -match "\\$_\\" })
  }

if (-not $pyFiles -or $pyFiles.Count -eq 0) {
    Write-Host "No se encontraron archivos .py del proyecto para analizar." -ForegroundColor Yellow
    exit 0
}

# Extraer imports top-level (import x / from x import y)
$imports = $pyFiles |
  Select-String -Pattern '^\s*(from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)' |
  ForEach-Object { $_.Matches.Groups[2].Value.ToLower() } |
  Sort-Object -Unique

# Eliminar módulos estándar (stdlib) para no intentar instalarlos
$stdlib = @(
  "abc","argparse","array","asyncio","atexit","base64","binascii","bisect","bz2","calendar","cgi","codecs",
  "collections","colorsys","compileall","configparser","contextlib","copy","csv","ctypes","dataclasses",
  "datetime","decimal","difflib","doctest","email","encodings","enum","errno","fnmatch","fractions","functools",
  "gc","getpass","glob","gzip","hashlib","heapq","hmac","html","http","importlib","inspect","io","ipaddress",
  "itertools","json","keyword","linecache","locale","logging","lzma","marshal","math","mimetypes","mmap",
  "multiprocessing","netrc","numbers","operator","os","pathlib","pickle","pkgutil","platform","plistlib",
  "pprint","queue","random","re","runpy","sched","select","shlex","shutil","site","socket","ssl","stat","string",
  "struct","subprocess","sys","sysconfig","tarfile","tempfile","textwrap","threading","time","tkinter","tokenize",
  "traceback","types","typing","unicodedata","urllib","uuid","warnings","weakref","webbrowser","xml","zipfile","zlib"
)

$imports = $imports | Where-Object { $_ -and ($stdlib -notcontains $_) }

# Quitar imports obviamente basura (por seguridad extra)
$deny = @("__future__","__main__","builtins","this")
$imports = $imports | Where-Object { $deny -notcontains $_ }

Write-Host "Imports detectados (filtrados):" -ForegroundColor Yellow
if ($imports.Count -eq 0) {
    Write-Host " - (ninguno fuera de la stdlib)" -ForegroundColor DarkYellow
    exit 0
}
$imports | ForEach-Object { Write-Host " - $_" }

# -----------------------------
# 3) Mapear import -> paquete pip
# -----------------------------
$map = @{
  "pil"   = "pillow"
  "cv2"   = "opencv-python"
  "bs4"   = "beautifulsoup4"
  "yaml"  = "pyyaml"
  "sklearn" = "scikit-learn"
  "crypto"  = "pycryptodome"
}

$resolved = foreach ($lib in $imports) {
  if ($map.ContainsKey($lib)) { $map[$lib] } else { $lib }
}
$resolved = $resolved | Sort-Object -Unique

# -----------------------------
# 4) Verificar instalados rápido y seguro
# -----------------------------
Write-Host "`nComprobando librerias instaladas..." -ForegroundColor Cyan

# Lista de paquetes instalados via pip (rápido)
$installed = pip list --format=freeze 2>$null |
  ForEach-Object { ($_ -split "==")[0].ToLower().Trim() } |
  Where-Object { $_ }

# Determinar faltantes
$missing = $resolved | Where-Object { $installed -notcontains $_ }

# Guardrail: si detecta demasiadas dependencias, NO instalar nada
$maxAllowed = 12
if ($resolved.Count -gt $maxAllowed) {
    Write-Host "`nSe detectaron demasiadas dependencias ($($resolved.Count))." -ForegroundColor Red
    Write-Host "Esto suele pasar cuando se analizan carpetas que no son del proyecto." -ForegroundColor Red
    Write-Host "Por seguridad, no se instalará nada. Revisa tu estructura o exclusiones." -ForegroundColor Yellow
    exit 1
}

if (-not $missing -or $missing.Count -eq 0) {
    Write-Host "`nTodas las librerias necesarias estan instaladas." -ForegroundColor Green
    exit 0
}

Write-Host "`nFaltan las siguientes librerias (pip):" -ForegroundColor Yellow
$missing | ForEach-Object { Write-Host " - $_" }

$confirm = Read-Host "¿Deseas instalarlas ahora? (s/n)"
if ($confirm -match '^(s|si|sí)$') {
    foreach ($pkg in $missing) {
        Write-Host "Instalando $pkg..." -ForegroundColor Cyan
        pip install $pkg
    }
    Write-Host "`nInstalacion completada." -ForegroundColor Green
} else {
    Write-Host "`nInstalacion cancelada por el usuario." -ForegroundColor Cyan
}

# Como Ejecutar:
# --------- Solo activar ENV (recomendado, rápido): .\release.ps1
# --------- Ejecutar y analizar: .\release.ps1 -analyze
