#!/usr/bin/env python3
"""local_code_builder_cli.py: Generador y constructor de código en hardware local (iGPU Vulkan).

Ejecuta el ciclo de construcción y auto-sanación en bucle cerrado a $0 tokens de API externa.
Uso: python3 local_code_builder_cli.py <test_file> <target_file> [--spec "resumen"] [--model qwen2.5-coder:7b]
"""

import argparse
import sys
from pathlib import Path

# Resolver ruta del código fuente (en repo local, cwd o en ~/.agents)
potential_roots = [
    Path.cwd(),
    Path(__file__).resolve().parent.parent.parent.parent,
    Path("/home/agustin/proyectos_software/agy-token-optimizer"),
]
for root in potential_roots:
    if (root / "src" / "adapters").is_dir() and str(root) not in sys.path:
        sys.path.insert(0, str(root))
        break


def main() -> None:
    from src.adapters.igpu_builder import OllamaVulkanCodeBuilder
    from src.adapters.slm_healer import OllamaVulkanSLMHealer
    from src.adapters.test_healer import OllamaTestFailureHealer
    from src.adapters.token_telemetry import SQLiteTokenTelemetry
    from src.application.local_build_pipeline import LocalBuildPipeline

    parser = argparse.ArgumentParser(
        description="Constructor de código local en iGPU Vulkan con validación TDD y auto-sanación."
    )
    parser.add_argument("test_file", help="Ruta al archivo de pruebas (ej. tests/test_feature.py)")
    parser.add_argument("target_file", help="Ruta al archivo de destino a implementar (ej. src/domain/feature.py)")
    parser.add_argument("--spec", default="", help="Resumen de especificación de la funcionalidad a construir")
    parser.add_argument(
        "--model", default="qwen2.5-coder:7b", help="Modelo de Ollama a utilizar (default: qwen2.5-coder:7b)"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:11434", help="URL base de Ollama (default: http://localhost:11434)"
    )

    args = parser.parse_args()

    test_path = Path(args.test_file).resolve()
    target_path = Path(args.target_file).resolve()

    if not test_path.exists():
        print(f"❌ Error: El archivo de tests '{test_path}' no existe. Define primero las pruebas TDD.")
        sys.exit(1)

    print(f"🚀 [iGPU Code Builder] Iniciando construcción en hardware local (Modelo: {args.model})...")
    print(f"   • Pruebas TDD : {test_path}")
    print(f"   • Destino     : {target_path}")

    # Instanciar adaptadores locales
    code_builder = OllamaVulkanCodeBuilder(
        base_url=args.base_url,
        default_model=args.model,
    )
    slm_healer = OllamaVulkanSLMHealer(endpoint_url=f"{args.base_url}/api/generate")
    test_healer = OllamaTestFailureHealer(endpoint_url=f"{args.base_url}/api/generate")

    telemetry = None
    try:
        telemetry = SQLiteTokenTelemetry()
    except Exception:
        pass

    pipeline = LocalBuildPipeline(
        code_builder=code_builder,
        slm_healer=slm_healer,
        test_healer=test_healer,
        telemetry=telemetry,
    )

    spec_summary = args.spec or f"Implementar {target_path.name} para satisfacer los tests en {test_path.name}"

    res = pipeline.run(
        test_file=str(test_path),
        target_file=str(target_path),
        spec_summary=spec_summary,
        model_name=args.model,
    )

    print("\n" + "=" * 65)
    if res.success:
        print("✅ [iGPU Code Builder] Implementación generada y validada en VERDE.")
        print(f"   • Trace ID         : {res.trace_id}")
        print(f"   • Archivo generado : {res.target_file}")
        print(f"   • Tokens ahorrados : {res.tokens_saved} ($0 tokens API externa)")
        print(f"   • Throughput iGPU  : {res.tokens_per_second:.1f} tok/s")
        print(f"   • Iteraciones TDD  : {res.iterations}")
        print(f"   • Latencia total   : {res.execution_time_ms:.1f} ms")
        print("=" * 65)
        sys.exit(0)
    else:
        print("❌ [iGPU Code Builder] No se pudo completar la construcción con éxito.")
        print(f"   • Trace ID: {res.trace_id}")
        print(f"   • Error: {res.error_message}")
        print(f"   • Iteraciones intentadas: {res.iterations}")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
