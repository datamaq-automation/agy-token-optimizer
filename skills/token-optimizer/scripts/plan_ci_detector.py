#!/usr/bin/env python3
"""
plan_ci_detector.py: Detector y resumidor de pipelines CI/CD pre-plan para AGY.
Parsea en CPU (< 5 ms) configuraciones de GitHub Actions, GitLab CI y Docker Compose,
extrayendo triggers y jobs principales en < 60 tokens a $0 tokens de API.
Uso: python3 plan_ci_detector.py [directorio_repo]
"""

import re
import sys
from pathlib import Path


def detect_ci_cd_pipelines(root_dir: Path) -> dict:
    result = {"system": "Sin CI/CD Configurado", "workflows": [], "has_docker": False, "has_vps_deploy": False}

    # 1. GitHub Actions
    gh_workflows = root_dir / ".github" / "workflows"
    if gh_workflows.is_dir():
        result["system"] = "GitHub Actions"
        for yml in gh_workflows.glob("*.yml"):
            try:
                with open(yml, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                jobs = re.findall(r"^\s{2}([a-zA-Z0-9_-]+):\s*$", content, re.MULTILINE)
                # Extraer triggers
                triggers = []
                if "push:" in content or "push" in content:
                    triggers.append("push")
                if "pull_request:" in content or "pull_request" in content:
                    triggers.append("pr")
                if "workflow_dispatch:" in content:
                    triggers.append("manual")

                if "ssh" in content.lower() or "vps" in content.lower():
                    result["has_vps_deploy"] = True

                result["workflows"].append({"file": yml.name, "triggers": triggers, "jobs": jobs[:4]})
            except Exception:
                continue

    # 2. GitLab CI
    gitlab_ci = root_dir / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        result["system"] = "GitLab CI"
        try:
            with open(gitlab_ci, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            stages = re.findall(r"^\s*-\s*([a-zA-Z0-9_-]+)", content, re.MULTILINE)
            result["workflows"].append({"file": ".gitlab-ci.yml", "triggers": ["push"], "jobs": stages[:4]})
        except Exception:
            pass

    # 3. Docker / Compose
    if (
        (root_dir / "Dockerfile").exists()
        or (root_dir / "docker-compose.yml").exists()
        or (root_dir / "docker-compose.yaml").exists()
    ):
        result["has_docker"] = True

    return result


def format_ci_bundle(ci_data: dict) -> str:
    lines = [
        f"⚙️ [Pipeline CI/CD Detectado: {ci_data['system']}]",
    ]
    if ci_data["workflows"]:
        for wf in ci_data["workflows"][:3]:
            trig_str = ", ".join(wf["triggers"]) if wf["triggers"] else "push"
            jobs_str = ", ".join(wf["jobs"]) if wf["jobs"] else "default"
            lines.append(f"   • `{wf['file']}` [{trig_str}] -> Jobs: [{jobs_str}]")

    if ci_data["has_docker"]:
        lines.append("   🐳 Docker / Compose: Activo")
    if ci_data["has_vps_deploy"]:
        lines.append("   🌐 Despliegue Remoto a VPS: Configurado")

    if not ci_data["workflows"]:
        lines.append("ℹ️ No se detectó CI/CD remoto. (Recomendado: `agy-opt scaffold-ci` para crear pipeline)")

    return "\n".join(lines)


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    data = detect_ci_cd_pipelines(root)
    bundle = format_ci_bundle(data)

    print("=" * 70)
    print(bundle)
    print("=" * 70)


if __name__ == "__main__":
    main()
