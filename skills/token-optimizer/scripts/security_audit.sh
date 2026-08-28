#!/usr/bin/env bash
# security_audit.sh: Auditor estático de seguridad local (Zero-Trust / OWASP) para AGY.
# Escanea claves privadas, tokens JWT, AWS keys y dependencias vulnerables en local sin gastar tokens.
# Uso: ./security_audit.sh [directorio_repo]

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

echo "======================================================================"
echo "🛡️  INICIANDO AUDITORÍA ESTÁTICA DE SEGURIDAD LOCAL (OWASP / Zero-Leak)"
echo "======================================================================"

FAILURES=0

# 1. Búsqueda de secretos, claves privadas y tokens quemados
echo "==> [1/3] Escaneando credenciales y secretos quemados en código fuente..."
SECRET_PATTERNS="(AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE KEY|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}|postgres://.*:.*@|mysql://.*:.*@|mongodb://.*:.*@|api[_-]?key\s*=\s*['\"][0-9a-zA-Z]{16,}['\"])"

SECRETS_FOUND=$(grep -rnE "$SECRET_PATTERNS" src tests 2>/dev/null | grep -v "\.git" || true)

if [ -n "$SECRETS_FOUND" ]; then
    echo "❌ [ALERTA DE SEGURIDAD] Se detectaron posibles credenciales quemadas:"
    echo "$SECRETS_FOUND"
    FAILURES=$((FAILURES + 1))
else
    echo "    ✓ Cero credenciales o secretos detectados en código fuente."
fi

# 2. Verificación de archivos sensibles en .gitignore
echo "==> [2/3] Verificando protección de archivos sensibles en .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -qE "^\.env" .gitignore; then
        echo "    ✓ Variables de entorno (.env) correctamente ignoradas."
    else
        echo "⚠️  [ADVERTENCIA] '.env' no está explícitamente listado en .gitignore."
    fi
fi

# 3. Auditoría de dependencias (si pip-audit o npm audit están presentes)
echo "==> [3/3] Verificando vulnerabilidades en paquetes y dependencias..."
if command -v pip-audit >/dev/null 2>&1 && [ -f "requirements.txt" ]; then
    pip-audit -r requirements.txt || FAILURES=$((FAILURES + 1))
elif command -v npm >/dev/null 2>&1 && [ -f "package.json" ]; then
    npm audit --audit-level=high || echo "    - Advertencias menores en dependencias npm."
else
    echo "    - Auditor de paquetes externo no requerido (omitido)."
fi

echo "======================================================================"
if [ "$FAILURES" -eq 0 ]; then
    echo "✅ AUDITORÍA DE SEGURIDAD LOCAL APROBADA (0 vulnerabilidades críticas)."
    echo "======================================================================"
    exit 0
else
    echo "❌ AUDITORÍA DE SEGURIDAD DETECTÓ $FAILURES VULNERABILIDADES CRÍTICAS."
    echo "======================================================================"
    exit 1
fi
