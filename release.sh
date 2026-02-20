#!/bin/bash
venvName="ENV"
venvPath="$(dirname "$0")/$venvName"

if [ ! -d "$venvPath" ]; then
    echo " No se encontró el entorno virtual en: $venvPath"
    exit 1
fi

source "$venvPath/bin/activate"
echo " Entorno virtual activado."

echo -e "\n Analizando dependencias..."
imports=$(grep -h -R -E '^(from|import) ' "$(dirname "$0")"/*.py | awk '{print $2}' | cut -d. -f1 | sort -u)

echo " Dependencias detectadas:"
echo "$imports" | sed 's/^/ - /'

missing=()
for lib in $imports; do
    pip show "$lib" >/dev/null 2>&1 || missing+=("$lib")
done

if [ ${#missing[@]} -eq 0 ]; then
    echo " Todas las librerías están instaladas."
else
    echo -e "\n Faltan las siguientes librerías:"
    for lib in "${missing[@]}"; do echo " - $lib"; done
    read -p "¿Deseas instalarlas ahora? (s/n): " confirm
    if [[ "$confirm" == "s" ]]; then
        for lib in "${missing[@]}"; do
            echo "⬇ Instalando $lib..."
            pip install "$lib"
        done
    fi
fi
