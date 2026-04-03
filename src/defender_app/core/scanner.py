from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from defender_app.native.native_loader import NativeRiskEngine
from defender_app.native.wasm_adapter import WasmRiskEngine
from defender_app.utils.http_client import HTTPResult, request_url
from defender_app.utils.url_tools import build_endpoint_url, is_https

from .models import EndpointResult, Finding, ProjectConfig, ScanReport


@dataclass
class _SeverityWeights:
    low: int = 3
    medium: int = 8
    high: int = 17
    critical: int = 30


class BackendSecurityScanner:
    REQUIRED_HEADERS = {
        "x-content-type-options": "Set to nosniff.",
        "x-frame-options": "Set to DENY or SAMEORIGIN.",
        "content-security-policy": "Define a strict CSP for web responses.",
        "referrer-policy": "Set a restrictive referrer policy.",
        "permissions-policy": "Disable browser capabilities not needed.",
    }

    SENSITIVE_HINTS = (
        "admin",
        "internal",
        "debug",
        "private",
        "metrics",
        "actuator",
    )

    def __init__(self) -> None:
        self._weights = _SeverityWeights()
        self._native = NativeRiskEngine()
        self._wasm = WasmRiskEngine()

    @property
    def native_status(self) -> str:
        return self._native.load_result.summary()

    @property
    def native_messages(self) -> list[str]:
        messages = list(self._native.load_result.messages)
        if not self._wasm.enabled and self._wasm.error:
            messages.append(f"wasm: disabled ({self._wasm.error})")
        return messages

    def scan(self, config: ProjectConfig) -> ScanReport:
        endpoint_results: list[EndpointResult] = []

        if not config.endpoints:
            return ScanReport.from_results(
                project_name=config.project_name,
                backend_url=config.backend_url,
                endpoint_results=[],
            )

        for mapping in config.endpoints:
            endpoint_results.append(self._scan_endpoint(config, mapping.backend_path, mapping.normalized_method()))

        return ScanReport.from_results(
            project_name=config.project_name,
            backend_url=config.backend_url,
            endpoint_results=endpoint_results,
        )

    def _scan_endpoint(self, config: ProjectConfig, backend_path: str, method: str) -> EndpointResult:
        endpoint_url = build_endpoint_url(config.backend_url, backend_path)
        findings: list[Finding] = []

        if not is_https(config.backend_url):
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="high",
                    title="Backend does not use HTTPS",
                    details="Traffic can be intercepted or altered over plaintext HTTP.",
                    recommendation="Serve backend APIs over HTTPS and enforce TLS redirects.",
                )
            )

        main = request_url(
            endpoint_url,
            method=method,
            timeout=config.timeout_seconds,
            headers={"User-Agent": "DefenderScanner/0.1"},
        )

        findings.extend(self._analyze_main_response(backend_path, method, main))

        options = request_url(
            endpoint_url,
            method="OPTIONS",
            timeout=config.timeout_seconds,
            headers={"User-Agent": "DefenderScanner/0.1"},
        )
        findings.extend(self._analyze_allowed_methods(backend_path, options))

        if method == "GET":
            reflection = request_url(
                endpoint_url,
                method="GET",
                timeout=config.timeout_seconds,
                query={"defender_probe": "NERVIN_SCAN_TOKEN"},
                headers={"User-Agent": "DefenderScanner/0.1"},
            )
            findings.extend(self._check_reflection(backend_path, reflection))

        if config.aggressive_checks:
            findings.extend(self._check_rate_limit(backend_path, endpoint_url, method, config.timeout_seconds))

        base_score = self._score_findings(findings)
        native_delta = self._native.c_risk_boost(backend_path, len(findings))
        anomaly_delta = self._native.cpp_anomaly_signal(method, main.status_code)
        jitter = self._native.asm_jitter(abs(hash(endpoint_url)))
        score = base_score + native_delta + anomaly_delta + jitter
        score = self._wasm.adjust_score(score, len(findings))
        score = max(0, min(100, score))

        return EndpointResult(
            endpoint=backend_path,
            method=method,
            status_code=main.status_code,
            response_ms=main.response_ms,
            risk_score=score,
            findings=findings,
        )

    def _analyze_main_response(
        self,
        backend_path: str,
        method: str,
        response: HTTPResult,
    ) -> list[Finding]:
        findings: list[Finding] = []

        if response.status_code is None:
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="critical",
                    title="Endpoint unreachable",
                    details=response.error or "The endpoint did not respond.",
                    recommendation="Check firewall, DNS, service health, and network ACL rules.",
                )
            )
            return findings

        if response.status_code >= 500:
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="high",
                    title="Server error response",
                    details=f"Endpoint returned {response.status_code}.",
                    recommendation="Inspect backend logs and harden exception handling.",
                )
            )

        if response.status_code in {200, 201, 202, 204} and any(
            hint in backend_path.lower() for hint in self.SENSITIVE_HINTS
        ):
            has_auth_header = "www-authenticate" in response.headers
            if not has_auth_header:
                findings.append(
                    self._finding(
                        endpoint=backend_path,
                        severity="high",
                        title="Sensitive endpoint may be exposed",
                        details="Sensitive path responded without an auth challenge header.",
                        recommendation="Require strong authentication and RBAC checks.",
                    )
                )

        server_header = response.headers.get("server", "")
        if server_header and any(char.isdigit() for char in server_header):
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="low",
                    title="Server version disclosure",
                    details=f"Server header exposed: {server_header}",
                    recommendation="Suppress or generalize version disclosure in headers.",
                )
            )

        missing_headers = self._missing_security_headers(response.headers)
        for header_name in missing_headers:
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="medium",
                    title=f"Missing security header: {header_name}",
                    details=f"Header {header_name} was not found in the response.",
                    recommendation=self.REQUIRED_HEADERS[header_name],
                )
            )

        if method in {"PUT", "PATCH", "DELETE"} and response.status_code in {200, 201, 202, 204}:
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="medium",
                    title="State-changing endpoint reachable",
                    details=f"{method} returned success.",
                    recommendation="Ensure authentication, authorization, CSRF protections, and audit logs.",
                )
            )

        return findings

    def _analyze_allowed_methods(self, backend_path: str, options_response: HTTPResult) -> list[Finding]:
        findings: list[Finding] = []

        allow_header = options_response.headers.get("allow", "")
        if allow_header:
            allowed = {token.strip().upper() for token in allow_header.split(",") if token.strip()}
            dangerous = allowed.intersection({"TRACE", "TRACK"})
            if dangerous:
                findings.append(
                    self._finding(
                        endpoint=backend_path,
                        severity="high",
                        title="Dangerous HTTP methods enabled",
                        details=f"Server allow-list includes: {', '.join(sorted(dangerous))}",
                        recommendation="Disable TRACE/TRACK at load balancer and application layers.",
                    )
                )
            if "OPTIONS" not in allowed:
                findings.append(
                    self._finding(
                        endpoint=backend_path,
                        severity="low",
                        title="OPTIONS not declared in allow-list",
                        details="CORS and method negotiation can behave inconsistently.",
                        recommendation="Return a complete Allow header for predictable behavior.",
                    )
                )
        elif options_response.status_code is not None and options_response.status_code >= 400:
            findings.append(
                self._finding(
                    endpoint=backend_path,
                    severity="low",
                    title="OPTIONS probe failed",
                    details=f"Endpoint returned {options_response.status_code} for OPTIONS.",
                    recommendation="Confirm your gateway supports preflight/method discovery safely.",
                )
            )

        return findings

    def _check_reflection(self, backend_path: str, response: HTTPResult) -> list[Finding]:
        if response.status_code is None:
            return []

        token = "NERVIN_SCAN_TOKEN"
        content_type = response.headers.get("content-type", "")
        if token in response.body and ("text" in content_type or "json" in content_type):
            return [
                self._finding(
                    endpoint=backend_path,
                    severity="medium",
                    title="Potential input reflection",
                    details="Probe token was reflected in response output.",
                    recommendation="Apply strict input validation and output encoding policies.",
                )
            ]
        return []

    def _check_rate_limit(
        self,
        backend_path: str,
        endpoint_url: str,
        method: str,
        timeout: float,
    ) -> list[Finding]:
        safe_method = method if method in {"GET", "HEAD"} else "GET"
        statuses: list[int] = []

        for _ in range(4):
            sample = request_url(
                endpoint_url,
                method=safe_method,
                timeout=timeout,
                headers={"User-Agent": "DefenderScanner/0.1"},
            )
            if sample.status_code is not None:
                statuses.append(sample.status_code)

        if statuses and all(status not in {429, 503} for status in statuses):
            return [
                self._finding(
                    endpoint=backend_path,
                    severity="medium",
                    title="Rate-limit controls not detected",
                    details="Repeated probe did not trigger 429/503 throttling indicators.",
                    recommendation="Implement endpoint-aware rate limits at gateway and app layers.",
                )
            ]

        return []

    def _missing_security_headers(self, headers: dict[str, str]) -> Iterable[str]:
        for header in self.REQUIRED_HEADERS:
            if header not in headers:
                yield header

    def _score_findings(self, findings: list[Finding]) -> int:
        score = 0
        for finding in findings:
            score += self._severity_weight(finding.severity)
        return score

    def _severity_weight(self, severity: str) -> int:
        severity = severity.lower().strip()
        if severity == "critical":
            return self._weights.critical
        if severity == "high":
            return self._weights.high
        if severity == "medium":
            return self._weights.medium
        return self._weights.low

    def _finding(
        self,
        endpoint: str,
        severity: str,
        title: str,
        details: str,
        recommendation: str,
    ) -> Finding:
        return Finding(
            endpoint=endpoint,
            severity=severity,
            title=title,
            details=details,
            recommendation=recommendation,
        )
