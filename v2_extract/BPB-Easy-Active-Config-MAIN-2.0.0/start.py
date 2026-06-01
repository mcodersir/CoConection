# -*- coding: utf-8 -*-
"""BPB/Nova Easy Active Config v2 — few-click deploy, scan and tested config output."""
from __future__ import annotations

import json
import mimetypes
import os
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
UI_DIR = ROOT_DIR / "ui"
OUT_DIR = ROOT_DIR / "output"
CONFIG_FILE = ROOT_DIR / "deploy_config.json"
IP_LIST_FILE = ROOT_DIR / "output" / "saved_ips.txt"
OUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SRC_DIR))

from core import (  # noqa: E402
    ALL_CF_WORKER_PORTS,
    build_bpb_template_configs,
    choose_best,
    expand_scan_endpoints,
    fetch_url_text,
    generate_modified_configs,
    is_fetch_error,
    normalize_ip_list,
    parse_configs,
    random_cloudflare_ips,
    save_ip_scan_outputs,
    save_outputs,
    scan_endpoints,
    split_subscription_lines,
    test_configs,
)
from cloudflare_deployer import deploy_worker_script, enable_worker_subdomain_route, get_workers_subdomain, list_accounts, verify_token  # noqa: E402

APP_NAME = "BPB/Nova Easy Active Config v2"

SAFE_URLS = {
    "cloudflare_signup": "https://dash.cloudflare.com/sign-up",
    "cloudflare_dashboard": "https://dash.cloudflare.com/",
    "cloudflare_workers_pages": "https://dash.cloudflare.com/?to=/:account/workers-and-pages",
    "cloudflare_api_tokens": "https://dash.cloudflare.com/profile/api-tokens",
    "cloudflare_account_home": "https://dash.cloudflare.com/?to=/:account",
    "atomic_mail": "https://atomicmail.io/app/auth/sign-up",
    "mcoders_github": "https://github.com/mcodersir",
    "nova_proxy_source": "https://github.com/IRNova/Nova-Proxy",
}

BUNDLED_WORKER = ROOT_DIR / "integrated_sources" / "BPB_Worker_Panel_Bundle" / "worker.js"


def save_deploy_config(data: dict):
    try:
        payload = {
            "api_token": (data.get("api_token") or "").strip(),
            "account_id": (data.get("account_id") or "").strip(),
            "worker_name": (data.get("worker_name") or "bpb-panel").strip(),
            "uuid": (data.get("uuid") or "").strip(),
            "sub_path": (data.get("sub_path") or "sub").strip().strip("/") or "sub",
            "proxy_ip": (data.get("proxy_ip") or "").strip(),
            "subscription_url": (data.get("subscription_url") or "").strip(),
        }
        existing = load_deploy_config()
        existing.update(payload)
        CONFIG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_deploy_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_ip_list(ip_text: str):
    """Save IP list for future use."""
    try:
        ips = normalize_ip_list(ip_text)
        if ips:
            IP_LIST_FILE.write_text("\n".join(ips) + "\n", encoding="utf-8")
    except Exception:
        pass


def load_saved_ips() -> str:
    """Load previously saved IPs."""
    try:
        if IP_LIST_FILE.exists():
            return IP_LIST_FILE.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def find_free_port(start=8765, tries=60):
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free local port found")


class AppHandler(BaseHTTPRequestHandler):
    server_version = "BPBNovaEasyActiveConfig/2.0"

    def log_message(self, fmt, *args):
        return

    def _send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _sse_event(self, event: str, data: dict):
        msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        try:
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 8_000_000:
            raise ValueError("Request too large")
        raw = self.rfile.read(length).decode("utf-8", errors="ignore") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({
                "app": APP_NAME,
                "brand": "Built by mcoders",
                "mcoders": "https://github.com/mcodersir",
                "output_dir": str(OUT_DIR),
                "bundled_worker_present": BUNDLED_WORKER.exists(),
                "all_ports": ALL_CF_WORKER_PORTS,
                "links": SAFE_URLS,
                "saved_ips": load_saved_ips(),
            })
            return
        if self.path == "/api/open-output":
            open_folder(OUT_DIR)
            self._send_json({"ok": True})
            return
        if self.path == "/api/deploy-config":
            cfg = load_deploy_config()
            token = cfg.get("api_token", "")
            if token and len(token) > 4:
                cfg["api_token_masked"] = "*" * (len(token) - 4) + token[-4:]
            else:
                cfg["api_token_masked"] = token
            cfg.pop("api_token", None)
            self._send_json({"ok": True, "config": cfg, "saved_ips": load_saved_ips()})
            return
        if self.path == "/api/saved-ips":
            self._send_json({"ok": True, "ips": load_saved_ips()})
            return

        # Static file serving
        path = unquote(self.path.split("?", 1)[0])
        if path == "/":
            path = "/index.html"
        file_path = (UI_DIR / path.lstrip("/")).resolve()
        try:
            file_path.relative_to(UI_DIR.resolve())
        except Exception:
            self.send_error(403)
            return
        if not file_path.exists() or file_path.is_dir():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype == "application/javascript" else ""))
        self.send_header("Content-Length", str(len(data)))
        # CSP header that allows everything local but no unsafe-eval
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self' data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            if self.path == "/api/open-url":
                self.api_open_url()
            elif self.path == "/api/fetch":
                self.api_fetch()
            elif self.path == "/api/scan-ips":
                self.api_scan_ips()
            elif self.path == "/api/run":
                self.api_run_sse()
            elif self.path == "/api/cf-verify":
                self.api_cf_verify()
            elif self.path == "/api/cf-deploy":
                self.api_cf_deploy()
            elif self.path == "/api/save-ips":
                self.api_save_ips()
            else:
                self._send_json({"ok": False, "error": "Invalid API path."}, 404)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 500)

    def api_open_url(self):
        data = self._read_json()
        key = (data.get("key") or "").strip()
        url = SAFE_URLS.get(key)
        if not url:
            raise ValueError("Link not in safe list.")
        webbrowser.open(url)
        self._send_json({"ok": True, "url": url})

    def api_cf_verify(self):
        data = self._read_json()
        token = (data.get("api_token") or "").strip()
        if not token:
            raise ValueError("Enter Cloudflare API Token.")
        token_check = verify_token(token)
        accounts = list_accounts(token)
        if token_check.get("success"):
            save_data = {"api_token": token}
            acc_list = accounts.get("result", []) if accounts.get("success") else []
            if acc_list:
                save_data["account_id"] = acc_list[0].get("id", "")
            existing = load_deploy_config()
            existing.update(save_data)
            save_deploy_config(existing)
        self._send_json({
            "ok": bool(token_check.get("success")),
            "token": token_check,
            "accounts": accounts.get("result", []) if accounts.get("success") else [],
        })

    def api_cf_deploy(self):
        data = self._read_json()
        token = (data.get("api_token") or "").strip()
        account_id = (data.get("account_id") or "").strip()
        worker_name = (data.get("worker_name") or "bpb-panel").strip()
        uuid = (data.get("uuid") or "").strip()
        sub_path = (data.get("sub_path") or "sub").strip().strip("/") or "sub"
        proxy_ip = (data.get("proxy_ip") or "").strip()
        if not token or not account_id or not worker_name:
            raise ValueError("API Token, Account ID and Worker name required.")
        if not uuid:
            raise ValueError("UUID required for VLESS config.")
        if not BUNDLED_WORKER.exists():
            raise ValueError("worker.js not found.")
        result = deploy_worker_script(token, account_id, worker_name, BUNDLED_WORKER, uuid=uuid, sub_path=sub_path, proxy_ip=proxy_ip)
        subdomain_hint = ""
        if result.get("success"):
            sub_info = get_workers_subdomain(token, account_id)
            try:
                sub_name = (sub_info.get("result") or {}).get("subdomain")
                if sub_name:
                    subdomain_hint = f"https://{worker_name}.{sub_name}.workers.dev/{sub_path}"
            except Exception:
                pass
        if result.get("success"):
            save_deploy_config({
                "api_token": token, "account_id": account_id,
                "worker_name": worker_name, "uuid": uuid,
                "sub_path": sub_path, "proxy_ip": proxy_ip,
                "subscription_url": subdomain_hint,
            })
            enable_worker_subdomain_route(token, account_id, worker_name)
        self._send_json({
            "ok": bool(result.get("success")),
            "deploy": result,
            "worker_url_hint": subdomain_hint,
            "next_steps_fa": [
                "Worker deployed! Click the subscription URL below or copy it.",
                "Then go to Step 2 and click 'Start' to generate configs.",
            ]
        })

    def api_fetch(self):
        data = self._read_json()
        sub_url = (data.get("subscription_url") or "").strip()
        raw_text, fetch_error = fetch_url_text(sub_url, timeout=int(data.get("timeout") or 18))
        if fetch_error and not raw_text:
            # Even on fetch error, try to build template configs from saved UUID
            saved = load_deploy_config()
            uuid = saved.get("uuid", "")
            if uuid:
                template_configs = build_bpb_template_configs(sub_url, uuid, saved.get("sub_path", "sub"), saved.get("proxy_ip", ""))
                if template_configs:
                    self._send_json({
                        "ok": True, "total_lines": len(template_configs),
                        "supported_configs": len(template_configs),
                        "examples": [f"Template #{i+1}" for i in range(min(8, len(template_configs)))],
                        "saved": str(OUT_DIR / "base_configs.txt"),
                        "fetch_warning": f"Subscription fetch failed ({fetch_error}), but {len(template_configs)} template configs were generated from your UUID.",
                    })
                    (OUT_DIR / "base_configs.txt").write_text("\n".join(template_configs) + "\n", encoding="utf-8")
                    return
            self._send_json({"ok": False, "error": fetch_error, "total_lines": 0, "supported_configs": 0, "examples": []})
            return
        lines = split_subscription_lines(raw_text)
        parsed = parse_configs(lines)
        # Also add template configs if we have UUID
        saved = load_deploy_config()
        uuid = saved.get("uuid", "")
        extra = []
        if uuid and len(parsed) < 3:
            extra = build_bpb_template_configs(sub_url, uuid, saved.get("sub_path", "sub"), saved.get("proxy_ip", ""))
        all_lines = lines + extra
        (OUT_DIR / "base_configs.txt").write_text("\n".join(all_lines) + "\n", encoding="utf-8")
        total_parsed = len(parsed) + len(extra)
        self._send_json({
            "ok": True, "total_lines": len(all_lines),
            "supported_configs": total_parsed,
            "examples": [c.display_name for c in parsed[:8]] + [f"Template #{i+1}" for i in range(min(4, len(extra)))],
            "saved": str(OUT_DIR / "base_configs.txt"),
            "fetch_warning": fetch_error if fetch_error else None,
        })

    def api_scan_ips(self):
        data = self._read_json()
        timeout = int(data.get("timeout") or 5)
        workers = int(data.get("workers") or 48)
        limit = int(data.get("ip_limit") or 1500)
        ip_text = data.get("ip_text") or ""
        cidr_text = data.get("cidr_text") or ""
        random_count = int(data.get("random_count") or 0)
        ports = [int(p) for p in data.get("ports", []) if str(p).isdigit()] or [443]
        sni_host = (data.get("sni_host") or "speed.cloudflare.com").strip() or "speed.cloudflare.com"
        endpoints = expand_scan_endpoints(ip_text, cidr_text, random_count, ports, limit=limit)
        if not endpoints:
            raise ValueError("Enter IP, CIDR or enable random generation for scanning.")
        logs = []
        def progress(done, total, res):
            if done <= 12 or done == total or done % 25 == 0:
                logs.append(f"{done}/{total} | {'OK' if res.ok else 'FAIL'} | {res.endpoint} | {res.latency_ms}ms | {res.message}")
        results = scan_endpoints(endpoints, timeout=timeout, workers=workers, limit=limit, sni_host=sni_host, progress=progress)
        files = save_ip_scan_outputs(ROOT_DIR, endpoints, results)
        clean = [r.endpoint for r in results if r.ok]
        # Save clean IPs for future use
        if clean:
            (OUT_DIR / "saved_ips.txt").write_text("\n".join(clean) + "\n", encoding="utf-8")
        self._send_json({
            "ok": True, "candidate_count": len(endpoints),
            "working_count": len(clean), "clean_ips": clean[:1000],
            "top_results": [r.to_dict() for r in results[:40]],
            "files": files, "logs": logs,
        })

    def api_save_ips(self):
        """Save IP list for future use."""
        data = self._read_json()
        ip_text = data.get("ip_text") or ""
        save_ip_list(ip_text)
        self._send_json({"ok": True, "saved": ip_text.count("\n") + 1 if ip_text.strip() else 0})

    def api_run_sse(self):
        """SSE streaming version of /api/run — sends incremental results."""
        data = self._read_json()
        sub_url = (data.get("subscription_url") or "").strip()
        mode = data.get("mode") or "auto"
        timeout = int(data.get("timeout") or 6)
        workers = int(data.get("workers") or 32)
        limit = int(data.get("limit") or 1600)
        random_count = int(data.get("random_count") or 0)
        selected_ports = [int(p) for p in data.get("ports", []) if str(p).isdigit()]
        ip_list_text = data.get("ip_list") or ""

        # Nova Easy Mode: stronger defaults, fewer decisions for the user.
        if mode == "nova_easy":
            timeout = max(timeout, 7)
            workers = max(workers, 48)
            limit = max(limit, 2600)
            random_count = max(random_count, 420)
            if not selected_ports:
                selected_ports = [443, 8443, 2053, 2083, 2087, 2096]

        # Save IP list
        save_ip_list(ip_list_text)

        self._send_sse_start()

        logs = []
        warnings = []
        result_items = []

        def progress(done, total, res):
            if done <= 12 or done == total or done % 10 == 0:
                state = "OK" if res.ok else "FAIL"
                log_msg = f"{done}/{total} | {state} | {res.endpoint} | {res.latency_ms}ms | {res.message}"
                logs.append(log_msg)
                # Send incremental SSE event for each test result
                self._sse_event("progress", {
                    "done": done, "total": total,
                    "ok": res.ok, "endpoint": res.endpoint,
                    "latency_ms": res.latency_ms, "score": res.score,
                    "message": res.message,
                    "config": getattr(res, 'config', ''),
                    "config_name": getattr(res, 'config_name', ''),
                    "scheme": getattr(res, 'scheme', ''),
                })

        def expand_ports(endpoints):
            if not selected_ports:
                return endpoints
            expanded = []
            for ep in endpoints:
                try:
                    has_port = len(ep.rsplit(":", 1)) == 2 and ep.rsplit(":", 1)[1].isdigit()
                except Exception:
                    has_port = False
                if has_port:
                    expanded.append(ep)
                else:
                    expanded.extend([f"{ep}:{port}" for port in selected_ports])
            return list(dict.fromkeys(expanded))

        def collect_clean_endpoints():
            endpoints = normalize_ip_list(ip_list_text)
            # Also load saved IPs
            if (OUT_DIR / "clean_ips.txt").exists():
                endpoints.extend(normalize_ip_list((OUT_DIR / "clean_ips.txt").read_text(encoding="utf-8", errors="ignore")))
            if (OUT_DIR / "saved_ips.txt").exists():
                endpoints.extend(normalize_ip_list((OUT_DIR / "saved_ips.txt").read_text(encoding="utf-8", errors="ignore")))
            if random_count > 0:
                endpoints.extend(random_cloudflare_ips(random_count))
            expanded = expand_ports(list(dict.fromkeys(endpoints)))
            if mode == "nova_easy" and expanded:
                self._sse_event("phase", {"phase": "nova_prescan", "message": f"Nova pre-scan: testing {min(len(expanded), 900)} endpoint candidates before generating configs..."})
                pre_limit = min(len(expanded), 900)
                pre = scan_endpoints(expanded[:pre_limit], timeout=max(3, min(timeout, 8)), workers=workers, limit=pre_limit, sni_host="speed.cloudflare.com", progress=progress)
                files = save_ip_scan_outputs(ROOT_DIR, expanded[:pre_limit], pre)
                ok_eps = [r.endpoint for r in pre if r.ok][:90]
                if ok_eps:
                    (OUT_DIR / "saved_ips.txt").write_text("\n".join(ok_eps) + "\n", encoding="utf-8")
                    self._sse_event("phase", {"phase": "nova_prescan", "message": f"Nova pre-scan: {len(ok_eps)} clean endpoints selected."})
                    return ok_eps
                warnings.append("Nova pre-scan did not find strong endpoints; continuing with raw candidates.")
            return expanded

        # Send start event
        self._sse_event("start", {"message": "Nova Easy Mode: آماده‌سازی کانفیگ‌ها و تست واقعی اتصال..."})

        # --- Step 1: Get configs (NEVER FAIL - always produce configs) ---
        base_configs = []
        fetch_warning = None

        self._sse_event("phase", {"phase": "fetch", "message": "Fetching subscription..."})

        raw_text, fetch_error = fetch_url_text(sub_url, timeout=max(12, timeout + 8))

        if fetch_error:
            fetch_warning = fetch_error
            logs.append(f"[WARNING] Subscription fetch error: {fetch_error}")

        # Parse subscription content if available
        if raw_text and not is_fetch_error(raw_text):
            lines = split_subscription_lines(raw_text)
            parsed = parse_configs(lines)
            base_configs = [c.raw for c in parsed]
            if base_configs:
                (OUT_DIR / "base_configs.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._sse_event("phase", {"phase": "fetch", "message": f"Found {len(base_configs)} configs from subscription."})

        # If no configs from subscription, ALWAYS build template configs
        if not base_configs:
            saved_config = load_deploy_config()
            uuid = saved_config.get("uuid", "")
            proxy_ip = saved_config.get("proxy_ip", "")
            sub_path = saved_config.get("sub_path", "sub")

            if uuid:
                template_configs = build_bpb_template_configs(sub_url, uuid, sub_path, proxy_ip)
                if template_configs:
                    base_configs = template_configs
                    self._sse_event("phase", {"phase": "fetch", "message": f"Generated {len(template_configs)} template configs from UUID."})
                    warnings.append("Subscription was not available. Template configs generated from your UUID.")
                else:
                    warnings.append("Could not generate configs. Check your UUID and Worker deployment.")
            else:
                # Last resort: try to extract UUID from the subscription URL itself
                # The worker generates configs based on the URL hostname
                if sub_url:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(sub_url)
                    hostname = parsed_url.hostname or ""
                    if hostname:
                        # Generate minimal configs with a placeholder UUID - at least the structure is right
                        warnings.append("No UUID saved. Please deploy the Worker first (Step 1), then come back.")

        # If STILL no configs, we MUST NOT return 500 — return what we have with warnings
        if not base_configs:
            self._sse_event("done", {
                "ok": False, "phase": "error",
                "base_count": 0, "target_count": 0,
                "result_count": 0, "working_count": 0,
                "best": None, "top_results": [],
                "logs": logs, "warnings": warnings + [
                    "No configs found. Please:",
                    "1. Deploy the Worker (Step 1)",
                    "2. Or paste a valid subscription URL",
                ],
            })
            return

        self._sse_event("phase", {"phase": "configs_ready", "message": f"{len(base_configs)} base configs ready."})

        # --- Step 2: Test configs ---
        phase = "base"
        target_configs = base_configs[:limit]
        results = []

        if mode in {"auto", "base", "nova_easy"}:
            self._sse_event("phase", {"phase": "test_base", "message": f"Testing {len(target_configs)} base configs..."})
            results = test_configs(target_configs, timeout=timeout, workers=workers, limit=limit, progress=progress)
            if mode == "base" or (mode == "auto" and any(r.ok for r in results)) or (mode == "nova_easy" and any(r.ok and r.score >= 90 and r.latency_ms < 2500 for r in results)):
                best = choose_best(results)
                files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
                self._sse_event("done", {
                    "ok": True, "phase": phase,
                    "base_count": len(base_configs), "target_count": len(target_configs),
                    "result_count": len(results), "working_count": len([r for r in results if r.ok]),
                    "best": best.to_dict() if best else None,
                    "top_results": [r.to_dict() for r in results[:20]],
                    "files": files, "logs": logs, "warnings": warnings,
                })
                return

        # Clean IP mode or auto fallback
        phase = "clean_ip" if mode == "clean_ip" else "auto_clean_ip"
        endpoints = collect_clean_endpoints()

        if not endpoints:
            if results and any(r.ok for r in results):
                best = choose_best(results)
                files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
                self._sse_event("done", {
                    "ok": True, "phase": "base_partial",
                    "base_count": len(base_configs), "target_count": len(target_configs),
                    "result_count": len(results), "working_count": len([r for r in results if r.ok]),
                    "best": best.to_dict() if best else None,
                    "top_results": [r.to_dict() for r in results[:20]],
                    "files": files, "logs": logs,
                    "warnings": warnings + ["No clean IPs available; showing base results."],
                })
                return
            # Even with no endpoints and no working results, save the base configs
            best = choose_best(results) if results else None
            files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
            self._sse_event("done", {
                "ok": len(results) > 0, "phase": "no_clean_ip",
                "base_count": len(base_configs), "target_count": len(target_configs),
                "result_count": len(results), "working_count": len([r for r in results if r.ok]),
                "best": best.to_dict() if best else None,
                "top_results": [r.to_dict() for r in results[:20]],
                "files": files, "logs": logs,
                "warnings": warnings + [
                    "No clean IPs available and no working configs found.",
                    "Try: 1) Run IP Scanner first, 2) Enable random IP generation, 3) Try 'auto' mode.",
                ],
            })
            return

        self._sse_event("phase", {"phase": "test_clean_ip", "message": f"Testing {len(endpoints)} clean IPs with {len(base_configs)} configs..."})
        target_configs = generate_modified_configs(base_configs, endpoints, limit=limit)
        if not target_configs:
            # Fallback to base results
            best = choose_best(results) if results else None
            files = save_outputs(ROOT_DIR, base_configs, base_configs[:limit], results, best)
            self._sse_event("done", {
                "ok": len(results) > 0, "phase": "no_modified",
                "base_count": len(base_configs), "target_count": len(base_configs[:limit]),
                "result_count": len(results), "working_count": len([r for r in results if r.ok]),
                "best": best.to_dict() if best else None,
                "top_results": [r.to_dict() for r in results[:20]],
                "files": files, "logs": logs, "warnings": warnings,
            })
            return

        results = test_configs(target_configs, timeout=timeout, workers=workers, limit=limit, progress=progress)
        best = choose_best(results)
        files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
        self._sse_event("done", {
            "ok": True, "phase": phase,
            "base_count": len(base_configs), "target_count": len(target_configs),
            "result_count": len(results), "working_count": len([r for r in results if r.ok]),
            "best": best.to_dict() if best else None,
            "top_results": [r.to_dict() for r in results[:20]],
            "files": files, "logs": logs, "warnings": warnings,
        })


def open_folder(path: Path):
    path = Path(path).resolve()
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(path)])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def main():
    port = find_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"{APP_NAME} is running locally:")
    print(url)
    print("Close the window or press Ctrl+C to exit.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
