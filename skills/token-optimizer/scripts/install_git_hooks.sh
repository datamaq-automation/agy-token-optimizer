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

# 1. Pre-commit hook (Ultrarrápido: < 2 segundos sobre archivos en stage)
cat <<'HOOK_EOF' > "$HOOKS_DIR/pre-commit"
#!/usr/bin/env bash
set -e
echo "🛡️  [Git Hook: pre-commit] Validando formato e integridad sobre cambios staged (< 2s)..."

# 1. Obtener archivos modificados o agregados en el stage actual
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# 2. Verificación de archivos __init__.py staged (deben tener 0 bytes)
STAGED_INITS=$(echo "$STAGED_FILES" | grep "__init__\.py$" || true)
if [ -n "$STAGED_INITS" ]; then
    for f in $STAGED_INITS; do
        if [ -s "$f" ]; then
            echo "❌ [BLOQUEO PRE-COMMIT] El archivo $f no tiene 0 bytes."
            exit 1
        fi
    done
fi

# 3. Formateo y linter quirúrgico para Python sobre archivos en stage
PY_FILES=$(echo "$STAGED_FILES" | grep -E '\.py$' || true)
if [ -n "$PY_FILES" ] && command -v ruff >/dev/null 2>&1; then
    echo "$PY_FILES" | xargs ruff check --fix --quiet || true
    echo "$PY_FILES" | xargs ruff format --quiet || true
    echo "$PY_FILES" | xargs git add || true
fi

# 4. Formateo y linter quirúrgico para JS / TS / Vue sobre archivos en stage
JS_FILES=$(echo "$STAGED_FILES" | grep -E '\.(js|jsx|ts|tsx|vue)$' || true)
if [ -n "$JS_FILES" ] && command -v npx >/dev/null 2>&1; then
    if [ -f "package.json" ]; then
        npx eslint --fix $JS_FILES >/dev/null 2>&1 || true
        echo "$JS_FILES" | xargs git add || true
    fi
fi

echo "✅ [pre-commit] Formato quirúrgico e integridad verificados."
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
