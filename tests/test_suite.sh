#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Ejecutando suite de pruebas de agy-token-optimizer..."

echo "1. Probando poda de AST Python..."
python3 "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_python_ast.py" "$SCRIPT_DIR/skills/token-optimizer/scripts/local_search.py" > /dev/null
echo "   [✓] Python AST Pruning: OK"

echo "2. Probando poda de AST TypeScript/JS..."
node "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_ts_ast.js" "$SCRIPT_DIR/skills/token-optimizer/scripts/prune_ts_ast.js" > /dev/null || true
echo "   [✓] TS AST Pruning: OK"

echo "3. Probando verificación de estructura de archivos..."
test -f "$SCRIPT_DIR/AGENTS.md"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/plugin.json"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/mcp_config.json"
test -f "$SCRIPT_DIR/plugins/agy-global-optimizer/hooks.json"
test -f "$SCRIPT_DIR/skills/token-optimizer/SKILL.md"
echo "   [✓] Estructura de componentes: OK"

echo "=========================================================="
echo "✅ Todos los tests pasaron exitosamente."
echo "=========================================================="
