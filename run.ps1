# Lanzador (Windows): prepara el entorno virtual y abre imgtool.
#   .\run.ps1                       -> menu interactivo
#   .\run.ps1 convert --to webp     -> comando directo
#   .\run.ps1 -Activate            -> solo activar el entorno, sin menu
param(
    [string]$venvName = "ENV",
    [switch]$Activate,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ToolArgs
)

$ErrorActionPreference = "Stop"

$venvPath = Join-Path $PSScriptRoot $venvName
$python = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creando entorno virtual ($venvName)..." -ForegroundColor Cyan
    python -m venv $venvPath
}

& $python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando dependencias..." -ForegroundColor Cyan
    & $python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
}

# Activar siempre: el entorno queda activo en la consola al salir del menu
if ($env:VIRTUAL_ENV -ne $venvPath) {
    . (Join-Path $venvPath "Scripts\Activate.ps1")
    Write-Host "Entorno activado ($venvName)." -ForegroundColor Green
}

if ($Activate) { return }

& $python (Join-Path $PSScriptRoot "imgtool.py") @ToolArgs
