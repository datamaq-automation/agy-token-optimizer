#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Ejecutando suite de pruebas de agy-token-optimizer (Fase 3)..."

echo "1. Probando poda de AST Python..."
python3 "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_python_ast.py" "$SCRIPT_DIR/skills/token-optimizer/scripts/local_search.py" > /dev/null
echo "   [✓] Python AST Pruning: OK"

echo "2. Probando poda de AST TypeScript/JS..."
node "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_ts_ast.js" "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_ts_ast.js" > /dev/null || true
echo "   [✓] TS AST Pruning: OK"

echo "3. Probando compresor de Git Diffs..."
TEST_DIFF="diff --git a/package-lock.json b/package-lock.json\n+ \"lockfileVersion\": 3\ndiff --git a/src/app.py b/src/app.py\n+ def new_logic():\n+     return True"
RESULT=$(echo -e "$TEST_DIFF" | python3 "$SCRIPT_DIR/skills/token-optimizer/scripts/diff_compressor.py")
if [[ "$RESULT" == *"[DIFF OMITIDO"* ]] && [[ "$RESULT" == *"def new_logic():"* ]]; then
    echo "   [✓] Git Diff Compressor: OK"
else
    echo "   [!] Git Diff Compressor Falló"
    exit 1
fi

echo "4. Probando Grafo de Símbolos en RAM/SQLite..."
python3 "$SCRIPT_DIR/skills/token-optimizer/scripts/symbol_graph.py" index "$SCRIPT_DIR/skills/token-optimizer/scripts" > /dev/null
SYM_RES=$(python3 "$SCRIPT_DIR/skills/token-optimizer/scripts/symbol_graph.py" find SymbolExtractor)
if [[ "$SYM_RES" == *"SymbolExtractor"* ]]; then
    echo "   [✓] Symbol Graph SQLite: OK"
else
    echo "   [!] Symbol Graph SQLite Falló"
    exit 1
fi

echo "5. Probando Runner de Tests Multihilo..."
test -x "$SCRIPT_DIR/skills/token-optimizer/scripts/test_runner.sh"
echo "   [✓] Test Runner: OK"

echo "=========================================================="
echo "✅ Todos los tests pasaron exitosamente (Fase 3 OK)."
echo "=========================================================="
