#!/usr/bin/env bash
# Lanzador (Linux/macOS/WSL/Git Bash): prepara el entorno virtual y abre imgtool.
#   ./run.sh                      -> menu interactivo
#   ./run.sh convert --to webp    -> comando directo
#   source run.sh                 -> igual, y deja el entorno activado en la consola
#   source run.sh --activate      -> solo activar el entorno, sin menu

_imgtool_run() {
    local dir venv bin py
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*)
            # Git Bash en Windows: mismo venv que run.ps1
            venv="$dir/ENV"; bin="$venv/Scripts"; py="$bin/python.exe"
            [ -x "$py" ] || python -m venv "$venv" || return 1
            ;;
        *)
            # ENV/ suele ser el venv de Windows (Scripts/); en Linux se usa .venv/
            if [ -x "$dir/ENV/bin/python" ]; then venv="$dir/ENV"; else venv="$dir/.venv"; fi
            bin="$venv/bin"; py="$bin/python"
            if [ ! -x "$py" ]; then
                echo "Creando entorno virtual en $venv ..."
                python3 -m venv "$venv" || return 1
            fi
            ;;
    esac

    if ! "$py" -c "import PIL" 2>/dev/null; then
        echo "Instalando dependencias ..."
        "$py" -m pip install -r "$dir/requirements.txt" || return 1
    fi

    # Solo al usar 'source' la activacion sobrevive en la consola
    if [ "${BASH_SOURCE[0]}" != "$0" ]; then
        # shellcheck disable=SC1091
        source "$bin/activate"
        echo "Entorno activado ($(basename "$venv"))."
    fi

    if [ "${1:-}" = "--activate" ]; then return 0; fi
    "$py" "$dir/imgtool.py" "$@"
}

_imgtool_run "$@"
