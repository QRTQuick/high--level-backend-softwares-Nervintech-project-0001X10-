from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import EndpointMapping, ProjectConfig


def save_project(config: ProjectConfig, file_path: str) -> None:
    payload = asdict(config)
    path = Path(file_path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_project(file_path: str) -> ProjectConfig:
    path = Path(file_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    endpoints = [EndpointMapping(**item) for item in payload.get("endpoints", [])]

    return ProjectConfig(
        project_name=payload.get("project_name", "Unnamed"),
        frontend_url=payload.get("frontend_url", ""),
        backend_url=payload.get("backend_url", ""),
        endpoints=endpoints,
        timeout_seconds=float(payload.get("timeout_seconds", 5.0)),
        aggressive_checks=bool(payload.get("aggressive_checks", False)),
    )
