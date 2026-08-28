#!/usr/bin/env bash
# test_runner.sh: Ejecutor de pruebas multihilo concurrente para AGY con reporte denso de fallos.
# Usa todos los núcleos de CPU disponibles y elimina el ruido de tests aprobados.
# Uso: ./test_runner.sh [ruta_o_archivo_test]

TARGET="${1:-tests}"
CORES=$(nproc 2>/dev/null || echo 4)

echo "==> ⚡ Ejecutando suite de pruebas en paralelo ($CORES hilos de CPU)..."

if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -d "tests" ] || [[ "$TARGET" == *.py ]]; then
    # Python Pytest con detección de pytest-xdist
    if python3 -c "import xdist" >/dev/null 2>&1; then
        PYTEST_CMD="pytest -n $CORES --tb=short -q $TARGET"
    else
        PYTEST_CMD="pytest --tb=short -q $TARGET"
    fi
    
    OUTPUT=$($PYTEST_CMD 2>&1) || STATUS=$?
    
    if [ "${STATUS:-0}" -eq 0 ]; then
        echo "✅ [100% Tests Aprobados] $(echo "$OUTPUT" | tail -n 1)"
    else
        echo "❌ [FALLO EN TESTS] Reporte denso de errores:"
        echo "=========================================================="
        # Extraer solo las secciones de fallos / assertions
        echo "$OUTPUT" | grep -E "(FAILURES|FAILED|AssertionError|File \".*\", line |E   )" -A 2 || echo "$OUTPUT"
        echo "=========================================================="
        exit 1
    fi
elif [ -f "package.json" ]; then
    # Node / Vite / Vitest
    npm test -- --threads --reporter=compact 2>&1 || exit 1
else
    echo "[!] No se detectó framework de pruebas estándar (pytest o npm test)."
    exit 0
fi
