from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from defender_app.core.models import EndpointMapping, ProjectConfig
from defender_app.core.scanner import BackendSecurityScanner


class DefenderAPIHandler(BaseHTTPRequestHandler):
    scanner = BackendSecurityScanner()

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/scan":
            self._json(404, {"error": "not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8"))
            config = self._parse_config(payload)
        except Exception as err:
            self._json(400, {"error": f"invalid request: {err}"})
            return

        report = self.scanner.scan(config)
        response = {
            "report": report.to_dict(),
            "native_status": self.scanner.native_status,
            "native_notes": self.scanner.native_messages,
        }
        self._json(200, response)

    def _parse_config(self, payload: dict) -> ProjectConfig:
        endpoints = [EndpointMapping(**item) for item in payload.get("endpoints", [])]
        return ProjectConfig(
            project_name=payload.get("project_name", "API-Driven Scan"),
            frontend_url=payload.get("frontend_url", ""),
            backend_url=payload["backend_url"],
            endpoints=endpoints,
            timeout_seconds=float(payload.get("timeout_seconds", 5.0)),
            aggressive_checks=bool(payload.get("aggressive_checks", False)),
        )

    def log_message(self, fmt: str, *args) -> None:  # pragma: no cover
        return


def run_api(host: str = "127.0.0.1", port: int = 8088) -> None:
    server = ThreadingHTTPServer((host, port), DefenderAPIHandler)
    print(f"Defender API listening on http://{host}:{port}")
    print("POST /scan with ProjectConfig JSON payload")
    server.serve_forever()


if __name__ == "__main__":
    run_api()
