from __future__ import annotations

import unittest
from unittest.mock import patch

from defender_app.core.models import EndpointMapping, ProjectConfig
from defender_app.core.scanner import BackendSecurityScanner
from defender_app.utils.http_client import HTTPResult


class ScannerTests(unittest.TestCase):
    def test_scan_finds_defensive_gaps(self) -> None:
        config = ProjectConfig(
            project_name="Local",
            frontend_url="http://frontend.local",
            backend_url="http://api.local",
            endpoints=[
                EndpointMapping(frontend_path="/", backend_path="/health", method="GET"),
                EndpointMapping(frontend_path="/admin", backend_path="/api/v1/admin", method="GET"),
            ],
            timeout_seconds=2.0,
            aggressive_checks=True,
        )

        with patch("defender_app.core.scanner.request_url", side_effect=self._fake_request_url):
            scanner = BackendSecurityScanner()
            report = scanner.scan(config)

        self.assertEqual(len(report.endpoint_results), 2)
        self.assertGreater(report.total_score, 0)

        finding_titles = [
            finding.title
            for endpoint_result in report.endpoint_results
            for finding in endpoint_result.findings
        ]

        self.assertIn("Backend does not use HTTPS", finding_titles)
        self.assertIn("Dangerous HTTP methods enabled", finding_titles)

    def _fake_request_url(self, url: str, method: str = "GET", **kwargs) -> HTTPResult:
        method = method.upper()

        if method == "OPTIONS":
            return HTTPResult(
                status_code=204,
                headers={"allow": "GET,POST,TRACE"},
                body="",
                response_ms=4.0,
            )

        if method == "GET" and "defender_probe=NERVIN_SCAN_TOKEN" in url:
            return HTTPResult(
                status_code=200,
                headers={"content-type": "text/plain"},
                body="NERVIN_SCAN_TOKEN",
                response_ms=5.0,
            )

        if method == "GET" and url.endswith("/health"):
            return HTTPResult(
                status_code=200,
                headers={"x-frame-options": "DENY", "server": "nginx/1.24.0"},
                body="ok",
                response_ms=6.1,
            )

        if method == "GET" and url.endswith("/api/v1/admin"):
            return HTTPResult(
                status_code=200,
                headers={"content-type": "text/plain", "server": "gunicorn/20.1"},
                body="admin-panel",
                response_ms=7.4,
            )

        return HTTPResult(
            status_code=429,
            headers={"content-type": "text/plain"},
            body="rate limit",
            response_ms=2.0,
        )


if __name__ == "__main__":
    unittest.main()
