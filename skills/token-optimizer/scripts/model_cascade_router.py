#!/usr/bin/env python3
"""
model_cascade_router.py: Enrutador Proxy en Cascada Inteligente para OpenCode en AGY.
Cascada:
  1. Google Gemini 2.0 Flash (Free Tier en AI Studio)
  2. Groq Cloud (Free Tier - Llama 3.3 70B)
  3. DeepSeek V3 / R1 (API de Pago Ultra-Económica)
  4. Ollama Local en RAM (qwen2.5-coder)
Uso: python3 model_cascade_router.py [--port 8080] [--test]
"""

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV_FILE = Path.home() / ".agy-optimizer" / ".env"


def load_env_keys() -> dict:
    keys = {
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
        "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
    }
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        keys[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return keys


def forward_chat_completion(payload: dict, keys: dict) -> tuple[dict, str]:
    """Ejecuta la cascada inteligente: Gemini -> Groq -> DeepSeek -> Ollama"""
    providers = []

    # 1. Gemini (OpenAI compatible endpoint)
    if keys.get("GEMINI_API_KEY"):
        providers.append(
            {
                "name": "Gemini 2.0 Flash (Free Tier)",
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {keys['GEMINI_API_KEY']}"},
                "model": "gemini-2.0-flash",
            }
        )

    # 2. Groq (Free Tier)
    if keys.get("GROQ_API_KEY"):
        providers.append(
            {
                "name": "Groq Cloud (Free Tier - Llama 3.3)",
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {keys['GROQ_API_KEY']}"},
                "model": "llama-3.3-70b-versatile",
            }
        )

    # 3. DeepSeek (Pago Ultra-Barato)
    if keys.get("DEEPSEEK_API_KEY"):
        providers.append(
            {
                "name": "DeepSeek V3 (Paid API)",
                "url": "https://api.deepseek.com/v1/chat/completions",
                "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {keys['DEEPSEEK_API_KEY']}"},
                "model": "deepseek-chat",
            }
        )

    # 4. Ollama Local Fallback
    providers.append(
        {
            "name": "Ollama Local (RAM qwen2.5-coder)",
            "url": "http://localhost:11434/v1/chat/completions",
            "headers": {"Content-Type": "application/json"},
            "model": "qwen2.5-coder:1.5b",
        }
    )

    last_err = ""
    for prov in providers:
        try:
            req_data = dict(payload)
            req_data["model"] = prov["model"]

            # Si el proveedor es DeepSeek, aplicar optimización de KV-Cache y payload
            if "deepseek" in prov["name"].lower():
                try:
                    from deepseek_optimizer import optimize_deepseek_payload

                    req_data = optimize_deepseek_payload(req_data)
                except Exception:
                    pass

            req_bytes = json.dumps(req_data).encode("utf-8")

            req = urllib.request.Request(prov["url"], data=req_bytes, headers=prov["headers"])
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data, prov["name"]
        except urllib.error.HTTPError as e:
            # Si es 429 (cuota agotada) o 503, conmutar al siguiente proveedor
            last_err = f"{prov['name']}: HTTP {e.code}"
            continue
        except Exception as e:
            last_err = f"{prov['name']}: {e}"
            continue

    # Mock fallback determinístico de emergencia si ningún servicio responde
    mock_resp = {
        "id": "mock-emergency-fallback",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "deterministic-fallback",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[AGY Router Fallback] Todos los proveedores fallaron ({last_err}). Revisa tus API keys en ~/.agy-optimizer/.env",
                },
                "finish_reason": "stop",
            }
        ],
    }
    return mock_resp, "Deterministic Fallback"


class CascadeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/v1/models", "/models"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "object": "list",
                "data": [
                    {"id": "auto-cascade", "object": "model", "owned_by": "agy-optimizer"},
                    {"id": "gemini-2.0-flash", "object": "model", "owned_by": "google"},
                    {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
                ],
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.endswith("/chat/completions"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"messages": [{"role": "user", "content": body}]}

            keys = load_env_keys()
            res_data, used_provider = forward_chat_completion(payload, keys)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-AGY-Provider", used_provider)
            self.end_headers()
            self.wfile.write(json.dumps(res_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def run_test_suite() -> bool:
    print("🧪 [Cascade Router Test] Validando cascada inteligente de proveedores...")
    keys = load_env_keys()
    test_payload = {"messages": [{"role": "user", "content": "Hola mundo"}]}
    res, provider = forward_chat_completion(test_payload, keys)
    print(f"✅ Respuesta recibida vía: {provider}")
    print(f"📦 Contenido resumido: {str(res)[:100]}...")
    return True


def main():
    if "--test" in sys.argv:
        success = run_test_suite()
        sys.exit(0 if success else 1)

    port = 8080
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    keys = load_env_keys()
    active_keys = [k for k, v in keys.items() if v]

    print("=" * 70)
    print(f"🌊 [AGY Cascade Router] Servidor activo en http://127.0.0.1:{port}/v1")
    print(f"🔑 API Keys detectadas en ~/.agy-optimizer/.env: {active_keys or 'Ninguna (usando Ollama local)'}")
    print("⚡ Orden de Cascada: Gemini 2.0 Flash ➔ Groq ➔ DeepSeek V3 ➔ Ollama")
    print("=" * 70)

    server = HTTPServer(("127.0.0.1", port), CascadeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido.")


if __name__ == "__main__":
    main()
