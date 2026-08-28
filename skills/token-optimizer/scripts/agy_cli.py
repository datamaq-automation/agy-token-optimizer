#!/usr/bin/env python3
"""
agy_cli.py (agy-opt): Orquestador maestro y CLI sidecar unificado para Google Antigravity (AGY).
Consolida las 24 herramientas de optimización local en una interfaz CLI rápida y potente.
Uso:
  agy-opt preflight [dir]
  agy-opt inject <simbolo|archivo|query>
  agy-opt heal [test_file]
  agy-opt ci [dir]
  agy-opt stats
  agy-opt commit [dir]
  agy-opt diagram [dir]
  agy-opt audit [dir]
  agy-opt stubs [src_dir]
  agy-opt squeeze <archivo>
  agy-opt ramdisk [mount|sync|status]
  agy-opt draft "<instrucción>"
  agy-opt test-synth <archivo.py>
  agy-opt minify <archivo>
  agy-opt cache <query|save|stats>
  agy-opt rules [dir]
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

COMMANDS = {
    "preflight": "local_watcher.py",
    "inject": "context_injector.py",
    "heal": "self_healing_runner.py",
    "ci": "ci_local.sh",
    "stats": "token_tracker.py",
    "commit": "pr_bundle_compressor.py",
    "diagram": "arch_diagram.py",
    "audit": "security_audit.sh",
    "stubs": "stub_generator.py",
    "squeeze": "prompt_squeezer.py",
    "ramdisk": "ramdisk_manager.sh",
    "draft": "local_slm_draft.py",
    "test-synth": "unit_test_synthesizer.py",
    "minify": "ast_minifier.py",
    "cache": "semantic_response_cache.py",
    "rules": "adaptive_rules_engine.py",
    "search": "local_search.py",
    "symbols": "symbol_graph.py",
    "diff": "diff_compressor.py",
    "test": "test_runner.sh",
    "hooks": "install_git_hooks.sh",
    "scaffold": "spec_scaffold.py",
}


def print_help():
    print("""
======================================================================
 ⚡ AGY-OPT: ORQUESTADOR MAESTRO LOCAL PARA GOOGLE ANTIGRAVITY
======================================================================
Uso: agy-opt <comando> [argumentos]

Comandos Principales:
  preflight [dir]       Inicia sincronización continua en RAM y actualiza índices
  inject <símbolo>      Genera paquete de contexto quirúrgico (< 500 tokens)
  heal [test_file]      Ejecuta auto-sanación en bucle cerrado con SLM local
  ci [dir]              Corre el pipeline Zero-Trust CI de 5 etapas (~1.5s)
  stats                 Muestra dashboard de tokens y dólares (USD) ahorrados
  commit [dir]          Genera mensaje de commit convencional y resumen de PR
  diagram [dir]         Genera diagrama Mermaid de arquitectura a $0 tokens
  audit [dir]           Auditoría estática de seguridad OWASP y secretos
  stubs [src_dir]       Genera stubs de tipos (.pyi) de 50 tokens
  rules [dir]           Genera y alinea AGENTS.md adaptativo para el proyecto
  draft "<prompt>"      Genera código base en RAM con qwen2.5-coder:1.5b
  cache query "<q>"     Consulta la memoria semántica persistente en RAM
  ramdisk [mount|sync]  Gestiona workspace ultra-rápido en /dev/shm (15 GB/s)
======================================================================
""")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"[!] Comando desconocido '{cmd}'. Usa 'agy-opt help' para ver la lista.")
        sys.exit(1)

    script_name = COMMANDS[cmd]
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"[!] Error: Script '{script_name}' no encontrado en {SCRIPTS_DIR}.")
        sys.exit(1)

    if script_name.endswith(".sh"):
        full_cmd = [str(script_path)] + args
    else:
        full_cmd = ["python3", str(script_path)] + args

    try:
        res = subprocess.run(full_cmd)
        sys.exit(res.returncode)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error ejecutando {cmd}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
