# Nervin Defender Console GUI User Guide

## 1. What This Tool Does

Nervin Defender Console is a desktop security scanner for backend systems.
You provide:

- A frontend URL
- A backend base URL
- A mapping of frontend pages to backend API paths

The app then runs defensive checks against mapped backend endpoints and gives:

- A readable text report
- A JSON report
- A per-endpoint risk score
- Actionable hardening recommendations

Use this only on infrastructure you own or are authorized to test.

## 2. Who Should Use It

This guide is for:

- Backend engineers
- DevSecOps teams
- QA/security testers running approved defensive assessments

## 3. Prerequisites

- Python 3.11+ installed
- Linux or macOS terminal access
- Project checked out locally

Optional:

- Native compiler toolchain (`gcc`, `g++`) for C/C++/ASM acceleration
- `wasmtime` Python package for optional WebAssembly score adjustment

## 4. First-Time Setup

From the project root:

```bash
cd /home/chisomlifeeke/Documents/high--level-backend-softwares-Nervintech-project-0001X10-
```

Build native modules:

```bash
./scripts/build_native.sh
```

Optional WebAssembly runtime:

```bash
python3 -m pip install -r requirements.txt
```

## 5. Start the GUI

Run:

```bash
./scripts/run_gui.sh
```

When the window opens, you will see:

- `Project` section at the top
- `Page to Backend Mapping` table in the middle
- `Scan Report` panel at the bottom
- Status line with native engine info and scan state

## 6. GUI Layout and Every Field

### 6.1 Project Section

- `Project Name`: Friendly label for the current scan profile.
- `Frontend URL`: Public frontend base URL to discover routes from.
- `Backend URL`: API base URL that will be scanned.
- `Timeout (s)`: Request timeout per endpoint probe.
- `Aggressive checks (extra rate-limit probe)`: Enables additional repeated probes to detect missing throttling behavior.
- `Discover Frontend Routes`: Pulls `<a href>` links from the frontend URL and auto-adds route mappings.
- `Run Security Scan`: Starts scan with current settings and mappings.

### 6.2 Page to Backend Mapping Section

- `Frontend Path`: UI route such as `/dashboard`.
- `Backend Path`: API path such as `/api/v1/admin`.
- `Method`: Request method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`).
- `Add Mapping`: Adds one row into the mapping table.
- `Remove Selected`: Deletes selected mapping rows.
- `Save Project`: Saves current configuration to JSON.
- `Load Project`: Loads a previously saved JSON profile.

Mapping table columns:

- `Frontend Page`
- `Backend Endpoint`
- `Method`

### 6.3 Scan Report Section

Shows:

- Human-readable report first
- Raw JSON report next
- Native engine notes at the end (for example missing optional modules)

### 6.4 Status Bar

Left side:

- Native engine load summary (C/C++/ASM availability)

Right side:

- Current action status (`Ready`, `Running security scan...`, `Scan complete...`)

## 7. Typical Workflow (Recommended)

1. Enter `Project Name`, `Frontend URL`, and `Backend URL`.
2. Set `Timeout (s)` to `5.0` as a baseline.
3. Click `Discover Frontend Routes` to auto-import known frontend paths.
4. Review generated rows and edit backend paths where needed.
5. Add missing endpoint mappings manually using `Frontend Path`, `Backend Path`, and `Method`.
6. Enable `Aggressive checks` only when you want extra rate-limit probing.
7. Click `Run Security Scan`.
8. Read findings in the `Scan Report` panel.
9. Save the project with `Save Project` so you can rerun later.

## 8. Example Mapping Strategy

Good mapping style:

- `/` -> `/health` (`GET`)
- `/dashboard` -> `/api/v1/admin` (`GET`)
- `/orders` -> `/api/v1/orders` (`POST`)
- `/orders/:id` (represented as `/orders`) -> `/api/v1/orders/{id}` (`GET`)

Tips:

- Map backend paths as realistically as possible.
- Include state-changing endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) to increase coverage.
- Keep mappings small and focused for each service.

## 9. How to Save and Load Projects

### Save

1. Click `Save Project`.
2. Choose a file path.
3. Save as `.json`.

### Load

1. Click `Load Project`.
2. Select a saved `.json`.
3. The form and mappings are restored automatically.

This is useful for:

- Team handoff
- Scheduled repeat scans
- Comparing risk trend over time

## 10. Understanding Scan Output

For each endpoint the report includes:

- Method and endpoint path
- HTTP status code
- Response latency
- Endpoint risk score
- Findings list with severity and fix guidance

Severity levels:

- `LOW`: Hygiene issue, usually quick hardening fix.
- `MEDIUM`: Security posture gap that should be prioritized.
- `HIGH`: Serious risk that can materially increase attack surface.
- `CRITICAL`: Endpoint unavailable or major defensive failure requiring urgent attention.

The report also shows:

- `Total Risk Score` for all mapped endpoints

Use the total score for trend tracking, not as a standalone pass/fail.

## 11. Checks the GUI Scan Performs

The scanner currently evaluates:

- HTTPS usage for backend URL
- Missing response security headers
- Dangerous methods in `Allow` header (`TRACE`, `TRACK`)
- Potential sensitive endpoint exposure patterns
- Basic input reflection for GET probe token
- Optional aggressive rate-limit signal checks

## 12. Troubleshooting

### App will not start

- Confirm Python version: `python3 --version`
- Run from project root
- Ensure script is executable: `chmod +x scripts/run_gui.sh`

### Native engines show as missing

- Run `./scripts/build_native.sh`
- Confirm files exist in `build/native`

### Scan shows endpoint unreachable

- Verify `Backend URL` is correct and resolvable
- Verify service is running and reachable from your machine
- Check VPN, DNS, firewall, proxy, and TLS settings

### No routes found during discovery

- Verify `Frontend URL` is reachable
- Route discovery only parses `<a href>` links in returned HTML
- SPA routes not present in static HTML may require manual mapping

### Timeout errors

- Increase `Timeout (s)` from `5.0` to `10.0` or higher for slow environments

## 13. Operational Best Practices

- Scan staging first, then production with approved change windows.
- Keep project JSON files in version control for auditability.
- Pair findings with ticket IDs and remediation owners.
- Re-run scans after each security fix to verify closure.
- Validate findings with backend logs and gateway policies before final decisions.

## 14. Safety and Legal

- Run only against systems you own or are explicitly authorized to assess.
- Follow your organization’s security testing policy and legal approval process.
- This tool is for defensive hardening and security posture improvement.

## 15. Quick Command Reference

From project root:

Build native modules:

```bash
./scripts/build_native.sh
```

Run GUI:

```bash
./scripts/run_gui.sh
```

Run CLI scan:

```bash
./scripts/run_cli_scan.sh sample_project.json
```

Run API mode:

```bash
./scripts/run_api.sh
```
