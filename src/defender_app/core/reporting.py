from __future__ import annotations

import json

from .models import ScanReport


def report_to_json(report: ScanReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def report_to_text(report: ScanReport) -> str:
    lines: list[str] = []
    lines.append(f"Project: {report.project_name}")
    lines.append(f"Backend: {report.backend_url}")
    lines.append(f"Generated: {report.generated_at}")
    lines.append(f"Total Risk Score: {report.total_score}")
    lines.append("")

    if not report.endpoint_results:
        lines.append("No endpoints were scanned.")
        return "\n".join(lines)

    for result in report.endpoint_results:
        lines.append(f"[{result.method}] {result.endpoint}")
        status = result.status_code if result.status_code is not None else "N/A"
        latency = (
            f"{result.response_ms:.2f}ms"
            if result.response_ms is not None
            else "N/A"
        )
        lines.append(f"  Status: {status}")
        lines.append(f"  Latency: {latency}")
        lines.append(f"  Endpoint Risk: {result.risk_score}")

        if not result.findings:
            lines.append("  Findings: none")
        else:
            lines.append("  Findings:")
            for finding in result.findings:
                lines.append(
                    f"    - ({finding.severity.upper()}) {finding.title}: {finding.details}"
                )
                lines.append(f"      Fix: {finding.recommendation}")
        lines.append("")

    return "\n".join(lines)
