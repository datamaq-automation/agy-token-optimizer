# Arquitectura del Sistema (Clean Architecture)

> **Tipo de Documento:** Diátaxis / Explanation
> **Propósito:** Explicar el modelo conceptual, dirección de dependencias y límites del dominio.

---

## 1. Reglas de Capas (Inward-Only)
```
[Infrastructure] ──► [Adapters] ──► [Application] ──► [Domain (Core)]
```
1. **Domain:** Entidades puras y puertos abstractos (`abc.ABC`). Cero dependencias externas.
2. **Application:** Casos de uso y orquestación de negocio.
3. **Adapters:** Controladores, gateways y repositorios que implementan puertos de dominio.
4. **Infrastructure:** Frameworks (FastAPI, SQLAlchemy, Docker, CLI).
