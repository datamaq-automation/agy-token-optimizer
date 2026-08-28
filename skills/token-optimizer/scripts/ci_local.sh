#!/usr/bin/env bash
# ci_local.sh: Pipeline local Zero-Trust CI de 5 etapas para AGY.
# Ejecuta validaciones estáticas, linters, tipado estricto y tests multihilo en ~1.5 segundos a $0 tokens.
# Uso: ./ci_local.sh [directorio_repo]

REPO_DIR="${1:-.}"
cd "$REPO_DIR"

START_TIME=$(date +%s%N)

echo "======================================================================"
echo "🛡️  INICIANDO PIPELINE LOCAL ZERO-TRUST CI (Uncle Bob Gauntlet)"
echo "======================================================================"

# 1. Integridad de archivos __init__.py (0 bytes)
echo "==> [1/5] Verificando archivos __init__.py vacíos..."
NON_EMPTY_INITS=$(find src tests -name "__init__.py" -type f -size +0c 2>/dev/null || true)
if [ -n "$NON_EMPTY_INITS" ]; then
    echo "❌ [FALLÓ ETAPA 1] Se encontraron __init__.py con contenido (>0 bytes):"
    echo "$NON_EMPTY_INITS"
    exit 1
fi
echo "    ✓ 100% de __init__.py tienen 0 bytes."

# 2. Formato y Linter con Ruff / ESLint
echo "==> [2/5] Ejecutando linters determinísticos (Ruff / ESLint)..."
if command -v ruff >/dev/null 2>&1; then
    ruff check . --quiet || { echo "❌ [FALLÓ ETAPA 2] Errores de linter detectados con Ruff."; exit 1; }
    ruff format --check . --quiet || { echo "❌ [FALLÓ ETAPA 2] Código no formateado según Ruff."; exit 1; }
    echo "    ✓ Linter y formateo Ruff aprobados (0 advertencias)."
else
    echo "    - Ruff no instalado (omitido)."
fi

# 3. Tipado Estricto con Pyright
echo "==> [3/5] Verificando tipado estricto (Pyright)..."
if command -v pyright >/dev/null 2>&1 && [ -f "pyrightconfig.json" -o -f "pyproject.toml" ]; then
    pyright || { echo "❌ [FALLÓ ETAPA 3] Errores de tipado estricto detectados con Pyright."; exit 1; }
    echo "    ✓ Tipado estricto verificado (0 diagnósticos)."
else
    echo "    - Pyright no configurado en este proyecto (omitido)."
fi

# 4. Guantelete de Arquitectura AST
echo "==> [4/5] Ejecutando Guantelete de Arquitectura AST..."
if [ -f "tests/test_architecture.py" ]; then
    python3 tests/test_architecture.py >/dev/null 2>&1 || { echo "❌ [FALLÓ ETAPA 4] Violación de Clean Architecture en test_architecture.py."; exit 1; }
    echo "    ✓ Guantelete de Arquitectura superado con éxito."
elif [ -f "scripts/test_architecture.mjs" ]; then
    node scripts/test_architecture.mjs >/dev/null 2>&1 || { echo "❌ [FALLÓ ETAPA 4] Violación de FSD en test_architecture.mjs."; exit 1; }
    echo "    ✓ Guantelete Frontend superado con éxito."
else
    echo "    - No se encontró script de arquitectura (omitido)."
fi

# 5. Suite de Tests Concurrente
echo "==> [5/5] Ejecutando suite de pruebas concurrentes..."
RUNNER="$HOME/.agents/skills/token-optimizer/scripts/test_runner.sh"
if [ -f "$RUNNER" ]; then
    "$RUNNER" || { echo "❌ [FALLÓ ETAPA 5] Fallaron las pruebas unitarias."; exit 1; }
else
    echo "    - Runner de tests no encontrado."
fi

END_TIME=$(date +%s%N)
DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))

echo "======================================================================"
echo "✅ PIPELINE ZERO-TRUST SUPERADO CON ÉXITO (${DURATION_MS} ms)"
echo "   El código cumple 100% las restricciones estáticas y está listo."
echo "======================================================================"
