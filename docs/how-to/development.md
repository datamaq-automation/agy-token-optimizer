# Guía de Desarrollo Local y Ejecución de la Suite (Diátaxis / How-To)

> **Propósito:** Guía paso a paso orientada a tareas para desarrolladores y agentes de IA.

---

## 1. Requisitos Previos
- Linux (Debian / Ubuntu / RHEL) con Python 3.10+ y Node.js.
- CPU con soporte de instrucciones AVX2 (para aceleración SIMD).
- Acceso a `/dev/shm` montado en RAM.

---

## 2. Instalación de la Suite Local
```bash
git clone https://github.com/datamaq-automation/agy-token-optimizer.git
cd agy-token-optimizer
./install.sh
```

---

## 3. Ejecución de Pruebas Automatizadas
Para verificar el 100% de las 45 herramientas locales:
```bash
./tests/test_suite.sh
```

---

## 4. Pipeline Zero-Trust CI
```bash
agy-opt ci .
```
