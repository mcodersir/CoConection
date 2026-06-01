# -*- coding: utf-8 -*-
"""Launch a local step-by-step web wizard for BPB Easy Active Config MAIN v9."""
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
OUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SRC_DIR))

from core import (  # noqa: E402
    ALL_CF_WORKER_PORTS,
    choose_best,
    expand_scan_endpoints,
    fetch_url_text,
    generate_modified_configs,
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

APP_NAME = "BPB Easy Active Config MAIN v9.0"

SAFE_URLS = {
    "cloudflare_signup": "https://dash.cloudflare.com/sign-up",
    "cloudflare_dashboard": "https://dash.cloudflare.com/",
    "cloudflare_workers_pages": "https://dash.cloudflare.com/?to=/:account/workers-and-pages",
    "cloudflare_api_tokens": "https://dash.cloudflare.com/profile/api-tokens",
    "cloudflare_account_home": "https://dash.cloudflare.com/?to=/:account",
    "atomic_mail": "https://atomicmail.io/app/auth/sign-up",
    "mcoders_github": "https://github.com/mcodersir",
}

BUNDLED_WORKER = ROOT_DIR / "integrated_sources" / "BPB_Worker_Panel_Bundle" / "worker.js"


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
    server_version = "BPBEasyActiveConfig/9.0"

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

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 8_000_000:
            raise ValueError("درخواست خیلی بزرگ است.")
        raw = self.rfile.read(length).decode("utf-8", errors="ignore") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({
                "app": APP_NAME,
                "brand": "ساخته شده توسط mcoders",
                "mcoders": "https://github.com/mcodersir",
                "no_cdn": True,
                "output_dir": str(OUT_DIR),
                "integrated_sources_dir": str(ROOT_DIR / "integrated_sources"),
                "bundled_worker_present": BUNDLED_WORKER.exists(),
                "bundled_worker_path": str(BUNDLED_WORKER),
                "all_ports": ALL_CF_WORKER_PORTS,
                "links": SAFE_URLS,
            })
            return
        if self.path == "/api/open-output":
            open_folder(OUT_DIR)
            self._send_json({"ok": True})
            return
        if self.path == "/api/open-integrated-folder":
            open_folder(ROOT_DIR / "integrated_sources")
            self._send_json({"ok": True})
            return

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
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype in {"application/javascript"} else ""))
        self.send_header("Content-Length", str(len(data)))
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
                self.api_run()
            elif self.path == "/api/cf-verify":
                self.api_cf_verify()
            elif self.path == "/api/cf-deploy":
                self.api_cf_deploy()
            else:
                self._send_json({"ok": False, "error": "مسیر API نامعتبر است."}, 404)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 500)

    def api_open_url(self):
        data = self._read_json()
        key = (data.get("key") or "").strip()
        url = SAFE_URLS.get(key)
        if not url:
            raise ValueError("لینک در لیست امن پروژه نیست.")
        webbrowser.open(url)
        self._send_json({"ok": True, "url": url})


    def api_cf_verify(self):
        data = self._read_json()
        token = (data.get("api_token") or "").strip()
        if not token:
            raise ValueError("API Token کلادفلر را وارد کن.")
        token_check = verify_token(token)
        accounts = list_accounts(token)
        self._send_json({
            "ok": bool(token_check.get("success")),
            "token": token_check,
            "accounts": accounts.get("result", []) if accounts.get("success") else [],
            "accounts_raw": accounts,
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
            raise ValueError("API Token، Account ID و نام Worker لازم است.")
        if not uuid:
            raise ValueError("UUID برای ساخت کانفیگ VLESS لازم است.")
        if not BUNDLED_WORKER.exists():
            raise ValueError("فایل داخلی BPB worker.js داخل integrated_sources/BPB_Worker_Panel_Bundle پیدا نشد.")
        result = deploy_worker_script(token, account_id, worker_name, BUNDLED_WORKER, uuid=uuid, sub_path=sub_path, proxy_ip=proxy_ip)
        subdomain_enable = None
        account_subdomain = None
        worker_url_hint = None
        if result.get("success"):
            subdomain_enable = enable_worker_subdomain_route(token, account_id, worker_name)
            account_subdomain = get_workers_subdomain(token, account_id)
            try:
                sub = (account_subdomain.get("result") or {}).get("subdomain")
                if sub:
                    worker_url_hint = f"https://{worker_name}.{sub}.workers.dev/{sub_path}"
            except Exception:
                worker_url_hint = None
        self._send_json({
            "ok": bool(result.get("success")),
            "deploy": result,
            "subdomain_enable": subdomain_enable,
            "account_subdomain": account_subdomain,
            "worker_url_hint": worker_url_hint,
            "next_steps_fa": [
                "اگر worker_url_hint ساخته شد، همان لینک را در مرورگر باز کن.",
                "اگر لینک ساخته نشد، در Cloudflare برو Workers & Pages → bpb-panel → Visit.",
                "داخل صفحه Worker مسیر /sub یا مسیر انتخاب‌شده را باز کن و Subscription را کپی کن."
            ]
        })

    def api_fetch(self):
        data = self._read_json()
        sub_url = (data.get("subscription_url") or "").strip()
        raw_text = fetch_url_text(sub_url, timeout=int(data.get("timeout") or 18))
        lines = split_subscription_lines(raw_text)
        parsed = parse_configs(lines)
        (OUT_DIR / "base_configs.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        self._send_json({
            "ok": True,
            "total_lines": len(lines),
            "supported_configs": len(parsed),
            "examples": [c.display_name for c in parsed[:8]],
            "saved": str(OUT_DIR / "base_configs.txt"),
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
            raise ValueError("برای اسکن باید IP، CIDR یا تولید تصادفی وارد کنی.")
        logs = []
        def progress(done, total, res):
            if done <= 12 or done == total or done % 25 == 0:
                logs.append(f"{done}/{total} | {'OK' if res.ok else 'FAIL'} | {res.endpoint} | {res.latency_ms}ms | {res.message}")
        results = scan_endpoints(endpoints, timeout=timeout, workers=workers, limit=limit, sni_host=sni_host, progress=progress)
        files = save_ip_scan_outputs(ROOT_DIR, endpoints, results)
        clean = [r.endpoint for r in results if r.ok]
        self._send_json({
            "ok": True,
            "candidate_count": len(endpoints),
            "working_count": len(clean),
            "clean_ips": clean[:1000],
            "top_results": [r.to_dict() for r in results[:40]],
            "files": files,
            "logs": logs,
        })

    def api_run(self):
        data = self._read_json()
        sub_url = (data.get("subscription_url") or "").strip()
        mode = data.get("mode") or "auto"
        timeout = int(data.get("timeout") or 6)
        workers = int(data.get("workers") or 32)
        limit = int(data.get("limit") or 1600)
        random_count = int(data.get("random_count") or 0)
        raw_text = fetch_url_text(sub_url, timeout=max(12, timeout + 8))
        lines = split_subscription_lines(raw_text)
        parsed = parse_configs(lines)
        base_configs = [c.raw for c in parsed]
        if not base_configs:
            raise ValueError("هیچ کانفیگ VLESS/Trojan/VMess قابل تستی داخل Subscription پیدا نشد.")

        selected_ports = [int(p) for p in data.get("ports", []) if str(p).isdigit()]
        logs = []
        def progress(done, total, res):
            if done <= 12 or done == total or done % 20 == 0:
                state = "OK" if res.ok else "FAIL"
                logs.append(f"{done}/{total} | {state} | {res.endpoint} | {res.latency_ms}ms | {res.message}")

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
            endpoints = normalize_ip_list(data.get("ip_list") or "")
            if (OUT_DIR / "clean_ips.txt").exists():
                endpoints.extend(normalize_ip_list((OUT_DIR / "clean_ips.txt").read_text(encoding="utf-8", errors="ignore")))
            if random_count > 0:
                endpoints.extend(random_cloudflare_ips(random_count))
            return expand_ports(list(dict.fromkeys(endpoints)))

        phase = "base"
        target_configs = base_configs[:limit]
        results = []

        # Smart mode: first validate original BPB configs. If one works, do not waste time on heavy IP generation.
        if mode in {"auto", "base"}:
            results = test_configs(target_configs, timeout=timeout, workers=workers, limit=limit, progress=progress)
            if mode == "base" or any(r.ok for r in results):
                best = choose_best(results)
                files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
                self._send_json({
                    "ok": True,
                    "phase": phase,
                    "base_count": len(base_configs),
                    "target_count": len(target_configs),
                    "result_count": len(results),
                    "working_count": len([r for r in results if r.ok]),
                    "best": best.to_dict() if best else None,
                    "top_results": [r.to_dict() for r in results[:20]],
                    "files": files,
                    "logs": logs,
                })
                return

        # Clean IP mode, or smart fallback when base has no usable result.
        phase = "clean_ip" if mode == "clean_ip" else "auto_clean_ip_fallback"
        endpoints = collect_clean_endpoints()
        if not endpoints:
            raise ValueError("برای حالت Clean IP باید IP وارد کنی، اسکنر IP را اجرا کنی، یا تولید تصادفی IP را فعال کنی.")
        target_configs = generate_modified_configs(base_configs, endpoints, limit=limit)
        if not target_configs:
            raise ValueError("از IPهای داده‌شده هیچ کانفیگ قابل تولیدی ساخته نشد.")
        results = test_configs(target_configs, timeout=timeout, workers=workers, limit=limit, progress=progress)
        best = choose_best(results)
        files = save_outputs(ROOT_DIR, base_configs, target_configs, results, best)
        self._send_json({
            "ok": True,
            "phase": phase,
            "base_count": len(base_configs),
            "target_count": len(target_configs),
            "result_count": len(results),
            "working_count": len([r for r in results if r.ok]),
            "best": best.to_dict() if best else None,
            "top_results": [r.to_dict() for r in results[:20]],
            "files": files,
            "logs": logs,
        })


def open_folder(path: Path):
    path = Path(path).resolve()
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
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
    print("برای خروج، پنجره را ببند یا Ctrl+C بزن.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nخروج.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
