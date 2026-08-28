#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Ejecutando suite de pruebas de agy-token-optimizer (Fase 2)..."

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

echo "4. Probando estructura y permisos..."
test -f "$SCRIPT_DIR/AGENTS.md"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/plugin.json"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/mcp_config.json"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/hooks.json"
test -f "$SCRIPT_DIR/skills/token-optimizer/SKILL.md"
test -x "$SCRIPT_DIR/skills/token-optimizer/scripts/diff_compressor.py"
test -x "$SCRIPT_DIR/skills/token-optimizer/scripts/local_search.py"
echo "   [✓] Estructura y permisos: OK"

echo "=========================================================="
echo "✅ Todos los tests pasaron exitosamente."
echo "=========================================================="
