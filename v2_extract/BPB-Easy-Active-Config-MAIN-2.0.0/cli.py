# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from core import (  # noqa: E402
    choose_best,
    expand_scan_endpoints,
    fetch_url_text,
    generate_modified_configs,
    normalize_ip_list,
    random_cloudflare_ips,
    save_ip_scan_outputs,
    save_outputs,
    scan_endpoints,
    split_subscription_lines,
    parse_configs,
    test_configs,
)


def cmd_scan_ips(args):
    ip_text = Path(args.ips).read_text(encoding="utf-8", errors="ignore") if args.ips else ""
    cidr_text = Path(args.cidrs).read_text(encoding="utf-8", errors="ignore") if args.cidrs else ""
    ports = [int(x.strip()) for x in args.ports.split(",") if x.strip().isdigit()]
    endpoints = expand_scan_endpoints(ip_text, cidr_text, args.random, ports, limit=args.limit)
    if not endpoints:
        raise SystemExit("هیچ endpoint برای اسکن ساخته نشد.")
    print(f"[1/2] Endpointهای اسکن: {len(endpoints)}")
    def progress(done, total, res):
        if done <= 10 or done == total or done % 25 == 0:
            print(f"{done}/{total} {'OK' if res.ok else 'FAIL'} {res.endpoint} {res.latency_ms}ms {res.message}")
    results = scan_endpoints(endpoints, timeout=args.timeout, workers=args.workers, limit=args.limit, sni_host=args.sni, progress=progress)
    files = save_ip_scan_outputs(ROOT_DIR, endpoints, results)
    print(f"[2/2] IPهای سالم: {len([r for r in results if r.ok])}")
    print("خروجی:", files["clean"])


def cmd_run(args):
    print("[1/4] دریافت Subscription...")
    raw, fetch_error = fetch_url_text(args.sub, timeout=max(12, args.timeout + 8))
    if fetch_error and not raw:
        print(f"[WARNING] Subscription fetch error: {fetch_error}")
        raise SystemExit(f"خطا در دریافت Subscription: {fetch_error}")
    lines = split_subscription_lines(raw)
    parsed = parse_configs(lines)
    base = [c.raw for c in parsed]
    if not base:
        raise SystemExit("هیچ کانفیگ قابل تستی پیدا نشد.")
    print(f"[2/4] کانفیگ‌های پایه: {len(base)}")

    def progress(done, total, res):
        if done <= 10 or done == total or done % 20 == 0:
            print(f"{done}/{total} {'OK' if res.ok else 'FAIL'} {res.endpoint} {res.latency_ms}ms {res.message}")

    target = list(base)[:args.limit]
    print(f"[3/4] تست مستقیم BPB: {len(target)} کانفیگ")
    print("[4/4] تست اتصال واقعی‌تر...")
    results = test_configs(target, timeout=args.timeout, workers=args.workers, limit=args.limit, progress=progress)

    if args.mode in {"auto", "clean_ip"} and (args.mode == "clean_ip" or not any(r.ok for r in results)):
        print("[fallback] ساخت و تست کانفیگ با Clean IP...")
        endpoints = []
        if args.ips:
            endpoints.extend(normalize_ip_list(Path(args.ips).read_text(encoding="utf-8", errors="ignore")))
        elif (ROOT_DIR / "output" / "clean_ips.txt").exists():
            endpoints.extend(normalize_ip_list((ROOT_DIR / "output" / "clean_ips.txt").read_text(encoding="utf-8", errors="ignore")))
        if args.random > 0:
            endpoints.extend(random_cloudflare_ips(args.random))
        ports = [int(x.strip()) for x in args.ports.split(",") if x.strip().isdigit()]
        expanded = []
        for ep in endpoints:
            has_port = len(ep.rsplit(":", 1)) == 2 and ep.rsplit(":", 1)[1].isdigit()
            expanded.extend([ep] if has_port else [f"{ep}:{port}" for port in ports])
        target = generate_modified_configs(base, list(dict.fromkeys(expanded)), limit=args.limit)
        print(f"[fallback] کانفیگ تولیدشده: {len(target)}")
        results = test_configs(target, timeout=args.timeout, workers=args.workers, limit=args.limit, progress=progress)

    best = choose_best(results)
    files = save_outputs(ROOT_DIR, base, target, results, best)
    print("\n========== BEST CONFIG ==========")
    print(best.config if best else "پیدا نشد")
    print("=================================")
    print("خروجی:", files["best"])


def main():
    p = argparse.ArgumentParser(description="BPB Easy Active Config MAIN v9 CLI")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("scan-ips", help="Scan Cloudflare IP/Endpoint candidates")
    ps.add_argument("--ips", default="", help="IP file, one endpoint per line")
    ps.add_argument("--cidrs", default="", help="CIDR file, one range per line")
    ps.add_argument("--random", type=int, default=80, help="Generate random Cloudflare IP candidates")
    ps.add_argument("--ports", default="443,8443,2053,2083,2087,2096", help="Comma-separated ports")
    ps.add_argument("--sni", default="speed.cloudflare.com")
    ps.add_argument("--timeout", type=int, default=5)
    ps.add_argument("--workers", type=int, default=48)
    ps.add_argument("--limit", type=int, default=800)
    ps.set_defaults(func=cmd_scan_ips)

    pr = sub.add_parser("run", help="Fetch BPB subscription, generate/test configs, save best")
    pr.add_argument("--sub", required=True, help="BPB subscription URL")
    pr.add_argument("--mode", choices=["auto", "base", "clean_ip"], default="auto")
    pr.add_argument("--ips", default="", help="Clean IP file, one endpoint per line. Defaults to output/clean_ips.txt if omitted.")
    pr.add_argument("--random", type=int, default=240, help="Generate random Cloudflare IP candidates for auto/clean_ip mode")
    pr.add_argument("--ports", default="443", help="Comma-separated ports for clean IP mode, e.g. 443,8443")
    pr.add_argument("--timeout", type=int, default=6)
    pr.add_argument("--workers", type=int, default=32)
    pr.add_argument("--limit", type=int, default=1500)
    pr.set_defaults(func=cmd_run)

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main() or 0)
