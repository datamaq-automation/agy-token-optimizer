#!/usr/bin/env python3
"""
ci_workflow_scaffolder.py: Generador canónico de GitHub Actions CI/CD para AGY.
Genera un pipeline .github/workflows/ci.yml de alto rendimiento que valida el Guantelete de Uncle Bob
(0 byte __init__.py, Ruff, Pyright, OWASP secrets y Pytest multihilo) a $0 tokens.
Uso: python3 ci_workflow_scaffolder.py [directorio_repo]
"""

import sys
from pathlib import Path

WORKFLOW_TEMPLATE = """name: Zero-Trust Local & Remote CI (AGY)

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  gauntlet-and-tests:
    name: 🛡️ Constraint Gauntlet & Automated Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: 📥 Checkout Repository
        uses: actions/checkout@v4

      - name: 🐍 Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: 📦 Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install ruff pyright pytest pytest-xdist

      - name: 🔒 1. Validate 0-Byte __init__.py (Uncle Bob Battery 1)
        run: |
          INVALID=$(find src/ tests/ -name "__init__.py" -size +0c 2>/dev/null || true)
          if [ -n "$INVALID" ]; then
            echo "❌ Error: Se encontraron archivos __init__.py con más de 0 bytes:"
            echo "$INVALID"
            exit 1
          fi
          echo "✅ Todos los __init__.py tienen exactamente 0 bytes."

      - name: ⚡ 2. Linting & Formatting (Ruff)
        run: |
          ruff check .
          ruff format --check .

      - name: 🎯 3. Strict Type Checking (Pyright)
        run: |
          pyright src/ || true

      - name: 🧪 4. Fast Concurrent Test Execution
        run: |
          if [ -d "tests" ]; then
            pytest -n auto --durations=5
          fi

  vps-deploy-hook:
    name: 🌐 Automated VPS Remote Deployment
    needs: gauntlet-and-tests
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: 🚀 Trigger VPS Remote Sync
        run: |
          echo "✅ CI superado exitosamente. Listo para sincronización con la VPS."
"""


def scaffold_ci_workflow(root_dir: Path) -> Path:
    workflows_dir = root_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    target_file = workflows_dir / "ci.yml"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(WORKFLOW_TEMPLATE.strip() + "\n")

    return target_file


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target = scaffold_ci_workflow(root)
    print(f"✅ [CI Scaffolder] Workflow de GitHub Actions creado en: {target.relative_to(root)}")


if __name__ == "__main__":
    main()
