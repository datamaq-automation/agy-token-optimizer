#!/usr/bin/env bash
# test_runner.sh: Ejecutor de pruebas multihilo concurrente para AGY con reporte denso de fallos.
# Usa todos los núcleos de CPU disponibles y elimina el ruido de tests aprobados.
# Uso: ./test_runner.sh [ruta_o_archivo_test]

TARGET="${1:-tests}"
CORES=$(nproc 2>/dev/null || echo 4)

echo "==> ⚡ Ejecutando suite de pruebas en paralelo ($CORES hilos de CPU)..."

# 1. Si existe suite personalizada del repositorio (ej. tests/test_suite.sh)
if [ -x "tests/test_suite.sh" ]; then
    ./tests/test_suite.sh || exit 1
    exit 0
fi

# 2. Framework Python
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -d "tests" ] || [[ "$TARGET" == *.py ]]; then
    if command -v pytest >/dev/null 2>&1 || python3 -m pytest --version >/dev/null 2>&1; then
        PY_CMD="pytest"
        command -v pytest >/dev/null 2>&1 || PY_CMD="python3 -m pytest"
        
        if python3 -c "import xdist" >/dev/null 2>&1; then
            PYTEST_CMD="$PY_CMD -n $CORES --tb=short -q $TARGET"
        else
            PYTEST_CMD="$PY_CMD --tb=short -q $TARGET"
        fi
        
        OUTPUT=$($PYTEST_CMD 2>&1) || STATUS=$?
        
        if [ "${STATUS:-0}" -eq 0 ]; then
            echo "✅ [100% Tests Aprobados] $(echo "$OUTPUT" | tail -n 1)"
        else
            echo "❌ [FALLO EN TESTS] Reporte denso de errores:"
            echo "=========================================================="
            echo "$OUTPUT" | grep -E "(FAILURES|FAILED|AssertionError|File \".*\", line |E   )" -A 2 || echo "$OUTPUT"
            echo "=========================================================="
            exit 1
        fi
    elif [ -d "tests" ]; then
        python3 -m unittest discover tests -q || exit 1
        echo "✅ [100% Tests Unittest Aprobados]"
    fi
elif [ -f "package.json" ]; then
    npm test -- --threads --reporter=compact 2>&1 || exit 1
else
    echo "[!] No se detectó suite de pruebas específica (omitido)."
    exit 0
fi
