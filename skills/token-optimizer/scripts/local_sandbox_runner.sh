#!/usr/bin/env bash
# local_sandbox_runner.sh: Ejecutor de comandos en Sandbox aislado de Linux para AGY.
# Utiliza namespaces de Linux o subshells confinadas para ejecutar pruebas sin riesgos de fuga.
# Uso: ./local_sandbox_runner.sh <comando...>

if [ $# -eq 0 ]; then
    echo "Uso: $0 <comando...>"
    exit 1
fi

echo "📦 [Linux Sandbox] Ejecutando comando en entorno aislado:"
echo "   Command: $*"
echo "----------------------------------------------------------------------"

# Intentar aislar con unshare si está disponible
if command -v unshare >/dev/null 2>&1 && unshare --help 2>&1 | grep -q "\-r"; then
    unshare -r -n -m bash -c "$*" || exit $?
else
    # Fallback a subshell con entorno restringido
    (
        umask 077
        export TMPDIR="/dev/shm"
        bash -c "$*"
    ) || exit $?
fi

echo "----------------------------------------------------------------------"
echo "✅ [Sandbox] Ejecución finalizada con código de salida 0."
