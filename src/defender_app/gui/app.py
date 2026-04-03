from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from defender_app.core.models import EndpointMapping, ProjectConfig
from defender_app.core.project_store import load_project, save_project
from defender_app.core.reporting import report_to_json, report_to_text
from defender_app.core.scanner import BackendSecurityScanner
from defender_app.utils.frontend_discovery import discover_frontend_routes


class DefenderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nervin Defender Console")
        self.root.geometry("1220x780")

        self.scanner = BackendSecurityScanner()

        self.project_name_var = tk.StringVar(value="My Secure Backend")
        self.frontend_url_var = tk.StringVar(value="https://example.com")
        self.backend_url_var = tk.StringVar(value="https://api.example.com")
        self.timeout_var = tk.StringVar(value="5.0")
        self.aggressive_var = tk.BooleanVar(value=False)

        self.new_frontend_path_var = tk.StringVar(value="/")
        self.new_backend_path_var = tk.StringVar(value="/")
        self.new_method_var = tk.StringVar(value="GET")

        self.status_var = tk.StringVar(value="Ready")
        self.native_var = tk.StringVar(value=f"Native engines: {self.scanner.native_status}")

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        top = ttk.LabelFrame(container, text="Project")
        top.pack(fill=tk.X, pady=6)

        ttk.Label(top, text="Project Name").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(top, textvariable=self.project_name_var, width=34).grid(
            row=0, column=1, padx=6, pady=6, sticky="we"
        )

        ttk.Label(top, text="Frontend URL").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(top, textvariable=self.frontend_url_var, width=34).grid(
            row=0, column=3, padx=6, pady=6, sticky="we"
        )

        ttk.Label(top, text="Backend URL").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(top, textvariable=self.backend_url_var, width=34).grid(
            row=1, column=1, padx=6, pady=6, sticky="we"
        )

        ttk.Label(top, text="Timeout (s)").grid(row=1, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(top, textvariable=self.timeout_var, width=10).grid(
            row=1, column=3, padx=6, pady=6, sticky="w"
        )

        ttk.Checkbutton(
            top,
            text="Aggressive checks (extra rate-limit probe)",
            variable=self.aggressive_var,
        ).grid(row=2, column=0, columnspan=2, padx=6, pady=6, sticky="w")

        ttk.Button(top, text="Discover Frontend Routes", command=self.discover_routes).grid(
            row=2, column=2, padx=6, pady=6, sticky="w"
        )
        ttk.Button(top, text="Run Security Scan", command=self.run_scan).grid(
            row=2, column=3, padx=6, pady=6, sticky="e"
        )

        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        map_frame = ttk.LabelFrame(container, text="Page to Backend Mapping")
        map_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        input_bar = ttk.Frame(map_frame)
        input_bar.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(input_bar, text="Frontend Path").pack(side=tk.LEFT, padx=4)
        ttk.Entry(input_bar, textvariable=self.new_frontend_path_var, width=20).pack(side=tk.LEFT)

        ttk.Label(input_bar, text="Backend Path").pack(side=tk.LEFT, padx=4)
        ttk.Entry(input_bar, textvariable=self.new_backend_path_var, width=20).pack(side=tk.LEFT)

        ttk.Label(input_bar, text="Method").pack(side=tk.LEFT, padx=4)
        method_combo = ttk.Combobox(
            input_bar,
            textvariable=self.new_method_var,
            values=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
            width=8,
            state="readonly",
        )
        method_combo.pack(side=tk.LEFT)

        ttk.Button(input_bar, text="Add Mapping", command=self.add_mapping).pack(side=tk.LEFT, padx=6)
        ttk.Button(input_bar, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(input_bar, text="Save Project", command=self.save_project_dialog).pack(side=tk.RIGHT, padx=6)
        ttk.Button(input_bar, text="Load Project", command=self.load_project_dialog).pack(side=tk.RIGHT, padx=6)

        columns = ("frontend", "backend", "method")
        self.mapping_tree = ttk.Treeview(map_frame, columns=columns, show="headings", height=10)
        self.mapping_tree.heading("frontend", text="Frontend Page")
        self.mapping_tree.heading("backend", text="Backend Endpoint")
        self.mapping_tree.heading("method", text="Method")
        self.mapping_tree.column("frontend", width=270)
        self.mapping_tree.column("backend", width=400)
        self.mapping_tree.column("method", width=100, anchor="center")
        self.mapping_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        report_frame = ttk.LabelFrame(container, text="Scan Report")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        self.report_text = tk.Text(report_frame, wrap=tk.WORD, font=("Courier", 10), bg="#10131a", fg="#dbe7ff")
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        status_bar = ttk.Frame(container)
        status_bar.pack(fill=tk.X)
        ttk.Label(status_bar, textvariable=self.native_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(status_bar, textvariable=self.status_var).pack(side=tk.RIGHT, padx=4)

    def add_mapping(self) -> None:
        frontend = self.new_frontend_path_var.get().strip() or "/"
        backend = self.new_backend_path_var.get().strip() or "/"
        method = self.new_method_var.get().strip().upper() or "GET"

        self.mapping_tree.insert("", tk.END, values=(frontend, backend, method))
        self.new_frontend_path_var.set(frontend)
        self.new_backend_path_var.set(backend)
        self.status_var.set("Mapping added")

    def remove_selected(self) -> None:
        selected = self.mapping_tree.selection()
        if not selected:
            return
        for item in selected:
            self.mapping_tree.delete(item)
        self.status_var.set("Selected mapping removed")

    def discover_routes(self) -> None:
        frontend_url = self.frontend_url_var.get().strip()
        if not frontend_url:
            messagebox.showerror("Missing URL", "Please enter a frontend URL first.")
            return

        self.status_var.set("Discovering routes from frontend...")
        worker = threading.Thread(target=self._discover_worker, args=(frontend_url,), daemon=True)
        worker.start()

    def _discover_worker(self, frontend_url: str) -> None:
        try:
            timeout = float(self.timeout_var.get() or 5.0)
        except ValueError:
            timeout = 5.0

        routes = discover_frontend_routes(frontend_url, timeout=timeout)

        def on_done() -> None:
            if not routes:
                self.status_var.set("No routes found (or frontend is unreachable)")
                return

            existing = {
                (self.mapping_tree.set(item, "frontend"), self.mapping_tree.set(item, "backend"), self.mapping_tree.set(item, "method"))
                for item in self.mapping_tree.get_children()
            }

            added = 0
            for route in routes:
                key = (route, route, "GET")
                if key in existing:
                    continue
                self.mapping_tree.insert("", tk.END, values=key)
                added += 1

            self.status_var.set(f"Discovered {len(routes)} routes, added {added} new mappings")

        self.root.after(0, on_done)

    def _collect_config(self) -> ProjectConfig | None:
        try:
            timeout = float(self.timeout_var.get() or 5.0)
        except ValueError:
            messagebox.showerror("Invalid timeout", "Timeout must be a number.")
            return None

        endpoints: list[EndpointMapping] = []
        for item in self.mapping_tree.get_children():
            values = self.mapping_tree.item(item).get("values", [])
            if len(values) != 3:
                continue
            endpoints.append(
                EndpointMapping(
                    frontend_path=str(values[0]),
                    backend_path=str(values[1]),
                    method=str(values[2]).upper(),
                )
            )

        return ProjectConfig(
            project_name=self.project_name_var.get().strip() or "Unnamed Project",
            frontend_url=self.frontend_url_var.get().strip(),
            backend_url=self.backend_url_var.get().strip(),
            endpoints=endpoints,
            timeout_seconds=timeout,
            aggressive_checks=bool(self.aggressive_var.get()),
        )

    def run_scan(self) -> None:
        config = self._collect_config()
        if config is None:
            return

        if not config.backend_url:
            messagebox.showerror("Missing backend URL", "Please add a backend URL before scanning.")
            return

        if not config.endpoints:
            messagebox.showerror("No endpoints", "Add at least one backend endpoint mapping first.")
            return

        self.status_var.set("Running security scan...")
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, "Scanning in progress...\n")

        worker = threading.Thread(target=self._scan_worker, args=(config,), daemon=True)
        worker.start()

    def _scan_worker(self, config: ProjectConfig) -> None:
        report = self.scanner.scan(config)
        text_report = report_to_text(report)
        json_report = report_to_json(report)
        native_notes = self.scanner.native_messages

        def on_done() -> None:
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert(tk.END, text_report)
            self.report_text.insert(tk.END, "\nJSON REPORT\n")
            self.report_text.insert(tk.END, json_report)
            if native_notes:
                self.report_text.insert(tk.END, "\n\nNATIVE ENGINE NOTES\n")
                for note in native_notes:
                    self.report_text.insert(tk.END, f"- {note}\n")
            self.status_var.set(f"Scan complete. Total score: {report.total_score}")

        self.root.after(0, on_done)

    def save_project_dialog(self) -> None:
        config = self._collect_config()
        if config is None:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Save Defender Project",
        )
        if not file_path:
            return

        save_project(config, file_path)
        self.status_var.set(f"Project saved: {file_path}")

    def load_project_dialog(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            title="Load Defender Project",
        )
        if not file_path:
            return

        try:
            config = load_project(file_path)
        except Exception as err:
            messagebox.showerror("Load error", f"Could not load project: {err}")
            return

        self.project_name_var.set(config.project_name)
        self.frontend_url_var.set(config.frontend_url)
        self.backend_url_var.set(config.backend_url)
        self.timeout_var.set(str(config.timeout_seconds))
        self.aggressive_var.set(config.aggressive_checks)

        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)

        for mapping in config.endpoints:
            self.mapping_tree.insert(
                "",
                tk.END,
                values=(mapping.frontend_path, mapping.backend_path, mapping.normalized_method()),
            )

        self.status_var.set(f"Project loaded: {file_path}")


def run_app() -> None:
    root = tk.Tk()
    app = DefenderApp(root)

    app.mapping_tree.insert("", tk.END, values=("/", "/health", "GET"))
    app.mapping_tree.insert("", tk.END, values=("/dashboard", "/api/v1/admin", "GET"))

    root.mainloop()
