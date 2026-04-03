from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class EndpointMapping:
    frontend_path: str
    backend_path: str
    method: str = "GET"

    def normalized_method(self) -> str:
        return (self.method or "GET").upper().strip()


@dataclass
class ProjectConfig:
    project_name: str
    frontend_url: str
    backend_url: str
    endpoints: list[EndpointMapping]
    timeout_seconds: float = 5.0
    aggressive_checks: bool = False


@dataclass
class Finding:
    endpoint: str
    severity: str
    title: str
    details: str
    recommendation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class EndpointResult:
    endpoint: str
    method: str
    status_code: int | None
    response_ms: float | None
    risk_score: int
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_ms": self.response_ms,
            "risk_score": self.risk_score,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass
class ScanReport:
    generated_at: str
    project_name: str
    backend_url: str
    total_score: int
    endpoint_results: list[EndpointResult]

    @classmethod
    def from_results(
        cls,
        project_name: str,
        backend_url: str,
        endpoint_results: list[EndpointResult],
    ) -> "ScanReport":
        total = sum(result.risk_score for result in endpoint_results)
        timestamp = datetime.now(timezone.utc).isoformat()
        return cls(
            generated_at=timestamp,
            project_name=project_name,
            backend_url=backend_url,
            total_score=total,
            endpoint_results=endpoint_results,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "backend_url": self.backend_url,
            "total_score": self.total_score,
            "endpoint_results": [result.to_dict() for result in self.endpoint_results],
        }
