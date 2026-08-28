#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🚀 Instalador de agy-token-optimizer (Antigravity Global)"
echo "=========================================================="

DEST_AGENTS="$HOME/.agents"
DEST_PLUGINS="$DEST_AGENTS/plugins"
DEST_SKILLS="$DEST_AGENTS/skills"
DEST_AGENTS_MD="$HOME/AGENTS.md"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 1. Creando directorios en $DEST_AGENTS..."
mkdir -p "$DEST_PLUGINS" "$DEST_SKILLS"

echo "==> 2. Instalando plugin global 'agy-global-optimizer'..."
mkdir -p "$DEST_PLUGINS/agy-global-optimizer"
cp -r "$SCRIPT_DIR/plugins/agy-global-optimizer/"* "$DEST_PLUGINS/agy-global-optimizer/"

echo "==> 3. Instalando skill 'token-optimizer'..."
mkdir -p "$DEST_SKILLS/token-optimizer"
cp -r "$SCRIPT_DIR/skills/token-optimizer/"* "$DEST_SKILLS/token-optimizer/"

echo "==> 4. Asignando permisos de ejecución a scripts..."
chmod +x "$DEST_SKILLS/token-optimizer/scripts/"* || true

echo "==> 5. Desplegando directivas globales en $DEST_AGENTS_MD..."
if [ -f "$DEST_AGENTS_MD" ]; then
    echo "    (Respaldando AGENTS.md previo en $DEST_AGENTS_MD.bak)"
    cp "$DEST_AGENTS_MD" "$DEST_AGENTS_MD.bak"
fi
cp "$SCRIPT_DIR/AGENTS.md" "$DEST_AGENTS_MD"

echo "==> 6. Verificando dependencias del sistema..."
command -v python3 >/dev/null 2>&1 && echo "  [✓] Python3 detectado" || echo "  [!] Python3 no encontrado"
command -v node >/dev/null 2>&1 && echo "  [✓] Node.js detectado" || echo "  [!] Node.js no encontrado (opcional para TS)"
command -v ruff >/dev/null 2>&1 && echo "  [✓] Ruff linter detectado" || echo "  [!] Ruff no encontrado (recomendado)"
command -v ollama >/dev/null 2>&1 && echo "  [✓] Ollama detectado" || echo "  [!] Ollama no encontrado (opcional para semantic search)"

echo "=========================================================="
echo "✅ ¡Instalación global completada con éxito!"
echo "   Ahora puedes usar /ask, /plan y /build en cualquier sesión de AGY."
echo "=========================================================="
