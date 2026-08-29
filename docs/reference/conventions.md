# Convenciones y Guantelete de Restricciones

> **Tipo de Documento:** Diátaxis / Reference
> **Propósito:** Definir estándares estáticos inmutables de código.

---

## 1. Las 5 Baterías del Guantelete
1. **`__init__.py` de 0 bytes:** 100% de los `__init__.py` con 0 bytes.
2. **Imports Absolutos:** Obligatorio `from src...` o `@/...`. Prohibido `from .` o `from ..`.
3. **Tipado Estricto:** Anotaciones explícitas en el 100% de parámetros y retornos. Prohibido `any`.
4. **Cero Evasiones:** Prohibido relajar directivas de tipos o linters.
5. **Zero Secretos:** Bloqueo estricto de credenciales en código.
