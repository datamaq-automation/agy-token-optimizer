#!/usr/bin/env bash
# install_git_hooks.sh: Instala ganchos de Git automatizados para el Guantelete de Restricciones.
# Uso: ./install_git_hooks.sh [directorio_repositorio]

REPO_DIR="${1:-.}"
GIT_DIR="$REPO_DIR/.git"

if [ ! -d "$GIT_DIR" ]; then
    echo "Error: No se encontró directorio .git en $REPO_DIR"
    exit 1
fi

HOOKS_DIR="$GIT_DIR/hooks"
mkdir -p "$HOOKS_DIR"

echo "==> Instalando Git Hooks de Gobernanza SDD en $HOOKS_DIR..."

# 1. Pre-commit hook
cat <<'HOOK_EOF' > "$HOOKS_DIR/pre-commit"
#!/usr/bin/env bash
set -e
echo "🛡️  [Git Hook: pre-commit] Validando integridad y formato..."

# 1. Verificación de archivos __init__.py vacíos (0 bytes)
NON_EMPTY_INITS=$(find src tests -name "__init__.py" -type f -size +0c 2>/dev/null || true)
if [ -n "$NON_EMPTY_INITS" ]; then
    echo "❌ [BLOQUEO PRE-COMMIT] Los siguientes archivos __init__.py no tienen 0 bytes:"
    echo "$NON_EMPTY_INITS"
    exit 1
fi

# 2. Linter determinístico si ruff está presente
if command -v ruff >/dev/null 2>&1; then
    ruff check --fix .
    ruff format .
fi

echo "✅ [pre-commit] Formato e integridad verificados."
HOOK_EOF
chmod +x "$HOOKS_DIR/pre-commit"

# 2. Pre-push hook
cat <<'HOOK_EOF' > "$HOOKS_DIR/pre-push"
#!/usr/bin/env bash
set -e
echo "🛡️  [Git Hook: pre-push] Ejecutando el Guantelete de Restricciones (Uncle Bob)..."

# 1. Guantelete de arquitectura AST si existe test_architecture.py
if [ -f "tests/test_architecture.py" ]; then
    python3 tests/test_architecture.py || { echo "❌ [BLOQUEO PRE-PUSH] Falló el Guantelete de Arquitectura."; exit 1; }
fi

# 2. Tipado estricto con Pyright si existe
if command -v pyright >/dev/null 2>&1 && [ -f "pyrightconfig.json" -o -f "pyproject.toml" ]; then
    pyright || { echo "❌ [BLOQUEO PRE-PUSH] Falló el chequeo estricto de tipos (Pyright)."; exit 1; }
fi

# 3. Suite de tests concurrente
if [ -f "$HOME/.agents/skills/token-optimizer/scripts/test_runner.sh" ]; then
    "$HOME/.agents/skills/token-optimizer/scripts/test_runner.sh" || { echo "❌ [BLOQUEO PRE-PUSH] Fallaron los tests unitarios."; exit 1; }
fi

echo "✅ [pre-push] Guantelete de Restricciones superado. Procediendo con el push."
HOOK_EOF
chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Ganchos 'pre-commit' y 'pre-push' instalados exitosamente en $REPO_DIR."
