from __future__ import annotations

import argparse
from pathlib import Path

from defender_app.core.project_store import load_project
from defender_app.core.reporting import report_to_text
from defender_app.core.scanner import BackendSecurityScanner
from defender_app.gui.app import run_app
from defender_app.server_api import run_api


def run_cli_scan(project_file: str) -> int:
    path = Path(project_file)
    if not path.exists():
        print(f"Project file not found: {path}")
        return 1

    config = load_project(str(path))
    scanner = BackendSecurityScanner()
    report = scanner.scan(config)
    print(report_to_text(report))

    notes = scanner.native_messages
    if notes:
        print("\nNative engine notes:")
        for note in notes:
            print(f"- {note}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Nervin Defender backend security console")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("gui", help="Launch Tkinter GUI")

    scan_parser = sub.add_parser("scan", help="Run scan from a saved project JSON")
    scan_parser.add_argument("--project", required=True, help="Path to project JSON file")

    api_parser = sub.add_parser("api", help="Run scanner in API mode")
    api_parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    api_parser.add_argument("--port", default=8088, type=int, help="Bind port")

    args = parser.parse_args()

    if args.command in (None, "gui"):
        run_app()
        return 0

    if args.command == "scan":
        return run_cli_scan(args.project)

    if args.command == "api":
        run_api(host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
