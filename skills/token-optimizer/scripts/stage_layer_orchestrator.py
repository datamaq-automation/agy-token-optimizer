#!/usr/bin/env python3
"""CLI Asistente de Staging y Commits Atómicos por Capas Arquitectónicas (agy-stage-layer).

Clasifica automáticamente los cambios en el árbol de trabajo git según la arquitectura
del proyecto (Clean Architecture / DDD en Python, FSD en Vue/TypeScript) para facilitar
commits atómicos por capas a $0 costo de fricción.
"""

import os
import sys

# Asegurar import de src.adapters.stage_layer_orchestrator desde cualquier ubicación
for candidate in [
    "/home/agustin/proyectos_software/agy-token-optimizer",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
    os.getcwd(),
]:
    if os.path.isdir(os.path.join(candidate, "src")) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from src.adapters.stage_layer_orchestrator import StageLayerOrchestrator  # noqa: E402


def print_help() -> None:
    print(
        """Uso de agy-stage-layer:
  agy-stage-layer status
      Muestra los archivos modificados agrupados por capa arquitectónica.

  agy-stage-layer stage <capa>
      Añade al staging únicamente los archivos de la capa indicada.
      Capas válidas: domain, application, ui, tooling

  agy-stage-layer commit <capa> "<mensaje>"
      Realiza el staging selectivo de la capa y confirma el commit con prefijo convencional.

Ejemplos:
  agy-stage-layer status
  agy-stage-layer stage domain
  agy-stage-layer commit domain "agregar entidad de usuario"
  agy-stage-layer commit ui "mejorar estilos de tarjeta"
"""
    )


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    subcmd = sys.argv[1].lower()
    orchestrator = StageLayerOrchestrator()

    if subcmd == "status":
        print(orchestrator.render_status_tui())

    elif subcmd == "stage":
        if len(sys.argv) < 3:
            print("Error: Debe especificar una capa (domain, application, ui, tooling).")
            print_help()
            sys.exit(1)
        layer = sys.argv[2].lower()
        staged = orchestrator.stage_layer(layer)
        if staged:
            print(f"✓ {len(staged)} archivo(s) agregados al stage para la capa '{layer}':")
            for f in staged:
                print(f"   • {f}")
        else:
            print(f"ℹ No hay archivos modificados para la capa '{layer}'.")

    elif subcmd == "commit":
        if len(sys.argv) < 4:
            print('Error: Uso: agy-stage-layer commit <capa> "<mensaje>"')
            sys.exit(1)
        layer = sys.argv[2].lower()
        message = sys.argv[3]

        success = orchestrator.commit_layer(layer, message)
        if success:
            formatted = orchestrator.format_commit_message(layer, message)
            print(f"✓ Commit atómico confirmado para capa '{layer}': {formatted}")
        else:
            print(f"❌ Error al crear commit para capa '{layer}'. Verifique que haya cambios pendientes.")
            sys.exit(1)
    else:
        print(f"Error: Subcomando desconocido '{subcmd}'.")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
