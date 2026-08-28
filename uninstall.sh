#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🧹 Desinstalador de agy-token-optimizer"
echo "=========================================================="

DEST_AGENTS="$HOME/.agents"
DEST_PLUGINS="$DEST_AGENTS/plugins/agy-global-optimizer"
DEST_SKILLS="$DEST_AGENTS/skills/token-optimizer"

echo "==> Removiendo plugin global..."
rm -rf "$DEST_PLUGINS"

echo "==> Removiendo skill token-optimizer..."
rm -rf "$DEST_SKILLS"

echo "==> Restaurando AGENTS.md si existe respaldo..."
if [ -f "$HOME/AGENTS.md.bak" ]; then
    mv "$HOME/AGENTS.md.bak" "$HOME/AGENTS.md"
    echo "    AGENTS.md restaurado desde .bak"
fi

echo "=========================================================="
echo "✅ Desinstalación completada."
echo "=========================================================="
