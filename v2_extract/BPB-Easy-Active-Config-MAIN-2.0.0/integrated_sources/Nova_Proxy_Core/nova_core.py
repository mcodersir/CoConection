# -*- coding: utf-8 -*-
"""
Nova Easy Core — transparent local integration inspired by IRNova/Nova-Proxy.

This module is intentionally readable. It does not contain obfuscated code.
It adds the "few-click" layer: better ranking, ready-to-import outputs, and
simple client exports from tested BPB/Nova-style links.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, unquote, urlparse

NOVA_VERSION = "2.0.0-nova"
NOVA_SAFE_PORTS = [443, 8443, 2053, 2083, 2087, 2096]
NOVA_DEFAULT_RANDOM_IPS = 420
NOVA_DEFAULT_WORKERS = 48
NOVA_DEFAULT_TIMEOUT = 7
NOVA_DEFAULT_LIMIT = 2600


def _getattr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _asdict(obj) -> dict:
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {
        "ok": _getattr(obj, "ok", False),
        "score": _getattr(obj, "score", 0),
        "latency_ms": _getattr(obj, "latency_ms", 999999),
        "endpoint": _getattr(obj, "endpoint", ""),
        "config": _getattr(obj, "config", ""),
        "message": _getattr(obj, "message", ""),
        "config_name": _getattr(obj, "config_name", ""),
        "scheme": _getattr(obj, "scheme", ""),
    }


def nova_rank_key(result) -> tuple:
    """Prefer configs that look really usable, not just TCP-open."""
    r = _asdict(result)
    ok = bool(r.get("ok"))
    msg = (r.get("message") or "").lower()
    scheme = (r.get("scheme") or "").lower()
    latency = int(r.get("latency_ms") or 999999)
    score = int(r.get("score") or 0)

    # True protocol-level signals are better than a plain TCP handshake.
    protocol_bonus = 0
    if "vless probe ok" in msg or "proxy responded" in msg:
        protocol_bonus += 80
    if "websocket 101" in msg or "ws" in msg:
        protocol_bonus += 35
    if scheme in {"vless", "trojan"}:
        protocol_bonus += 10
    if "tcp ok" in msg and "websocket" not in msg and "vless" not in msg:
        protocol_bonus -= 15

    # Lower latency is important but should not beat protocol-validity alone.
    return (not ok, -(score + protocol_bonus), latency)


def choose_nova_best(results: Sequence) -> Optional:
    items = [r for r in results if bool(_getattr(r, "ok", False))]
    if not items:
        return None
    return sorted(items, key=nova_rank_key)[0]


def working_results(results: Sequence, minimum_score: int = 50) -> List:
    items = [r for r in results if bool(_getattr(r, "ok", False))]
    strong = [r for r in items if int(_getattr(r, "score", 0) or 0) >= minimum_score]
    return sorted(strong or items, key=nova_rank_key)


def _strip_summary(config_text: str) -> str:
    """If best_active_config.txt includes a report box, return only the share link."""
    for line in (config_text or "").splitlines():
        s = line.strip()
        if s.startswith(("vless://", "trojan://", "vmess://", "ss://", "wireguard://")):
            return s
    return (config_text or "").strip()


def _safe_name(s: str) -> str:
    return (s or "Nova Node").replace("'", "").replace('"', "").strip()[:80] or "Nova Node"


def _clash_proxy_from_link(link: str, idx: int) -> Optional[str]:
    """Generate a basic Clash/Mihomo proxy entry for vless/trojan WS-TLS links.

    This is intentionally conservative: if a link uses unsupported transport,
    it is skipped instead of emitting a broken profile.
    """
    try:
        u = urlparse(link)
        scheme = u.scheme.lower()
        if scheme not in {"vless", "trojan"}:
            return None
        qs = parse_qs(u.query)
        net_type = (qs.get("type", qs.get("network", ["ws"]))[0] or "ws").lower()
        if net_type not in {"ws", "websocket"}:
            return None
        name = _safe_name(unquote(u.fragment or f"Nova-{scheme}-{idx}"))
        server = u.hostname or ""
        port = int(u.port or 443)
        sni = qs.get("sni", qs.get("host", [server]))[0] or server
        ws_host = qs.get("host", [sni])[0] or sni
        path = qs.get("path", ["/"])[0] or "/"
        if not path.startswith("/"):
            path = "/" + path
        if scheme == "vless":
            uuid = (u.username or "").strip()
            if not uuid:
                return None
            return f"""  - name: '{name}'
    type: vless
    server: {server}
    port: {port}
    uuid: {uuid}
    tls: true
    udp: true
    servername: {sni}
    network: ws
    ws-opts:
      path: '{path}'
      headers:
        Host: {ws_host}"""
        password = (u.username or "").strip()
        if not password:
            return None
        return f"""  - name: '{name}'
    type: trojan
    server: {server}
    port: {port}
    password: {password}
    tls: true
    udp: true
    sni: {sni}
    network: ws
    ws-opts:
      path: '{path}'
      headers:
        Host: {ws_host}"""
    except Exception:
        return None


def links_to_clash_meta_yaml(links: Sequence[str]) -> str:
    entries = []
    names = []
    for i, link in enumerate(links, 1):
        p = _clash_proxy_from_link(link, i)
        if not p:
            continue
        entries.append(p)
        first = p.splitlines()[0]
        name = first.split("name:", 1)[1].strip().strip("'") if "name:" in first else f"Nova-{i}"
        names.append(name)
    if not entries:
        return "# No compatible VLESS/Trojan WS-TLS links were available for Clash/Mihomo export.\n"
    names_yaml = "\n".join([f"      - '{n}'" for n in names])
    return f"""# Generated locally by mcoders BPB/Nova Easy v2
mixed-port: 7890
allow-lan: false
mode: rule
log-level: warning
ipv6: false

proxies:
{chr(10).join(entries)}

proxy-groups:
  - name: 'Nova Auto'
    type: url-test
    url: 'https://www.gstatic.com/generate_204'
    interval: 300
    tolerance: 120
    proxies:
{names_yaml}

rules:
  - MATCH,Nova Auto
"""


def write_nova_outputs(root: Path, base_configs: Sequence[str], generated_configs: Sequence[str], results: Sequence, best) -> dict:
    out_dir = Path(root) / "output"
    out_dir.mkdir(exist_ok=True)
    best = choose_nova_best(results) or best
    working = working_results(results)
    working_links = [_strip_summary(_getattr(r, "config", "")) for r in working]
    working_links = [x for x in working_links if x]
    best_link = _strip_summary(_getattr(best, "config", "")) if best else ""

    files = {
        "nova_best": out_dir / "nova_best_config_only.txt",
        "nova_working": out_dir / "nova_working_configs.txt",
        "nova_quick": out_dir / "nova_quick_import.txt",
        "nova_bundle": out_dir / "nova_bundle.json",
        "nova_report": out_dir / "nova_report_FA.md",
        "nova_clash": out_dir / "nova_clash_meta.yaml",
    }
    files["nova_best"].write_text((best_link + "\n") if best_link else "", encoding="utf-8")
    files["nova_working"].write_text("\n".join(working_links) + ("\n" if working_links else ""), encoding="utf-8")
    quick = []
    if best_link:
        quick += ["# BEST CONFIG — copy/import this first", best_link, ""]
    if working_links:
        quick += ["# BACKUP WORKING CONFIGS", *working_links[:30], ""]
    files["nova_quick"].write_text("\n".join(quick), encoding="utf-8")
    files["nova_clash"].write_text(links_to_clash_meta_yaml(working_links[:60]), encoding="utf-8")
    bundle = {
        "app": "BPB/Nova Easy Active Config",
        "version": NOVA_VERSION,
        "best": _asdict(best) if best else None,
        "working_count": len(working_links),
        "tested_count": len(results),
        "base_count": len(base_configs),
        "generated_count": len(generated_configs),
        "working_configs": working_links[:100],
        "notes": [
            "Use nova_best_config_only.txt for the fastest import.",
            "Use nova_working_configs.txt as backup configs.",
            "Use nova_clash_meta.yaml only if your client supports Clash/Mihomo YAML.",
        ],
    }
    files["nova_bundle"].write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [
        "# گزارش Nova Easy Mode",
        "",
        "ساخته شده توسط mcoders — https://github.com/mcodersir",
        "",
        f"- کانفیگ پایه: {len(base_configs)}",
        f"- کانفیگ تولیدشده/تست‌شده: {len(generated_configs)}",
        f"- نتیجه تست: {len(results)}",
        f"- کانفیگ سالم برای import: {len(working_links)}",
        "",
        "## خروجی اصلی",
        "",
        "اول فایل `nova_best_config_only.txt` را داخل Hiddify / NekoBox / v2rayN / Sing-box import کن.",
        "اگر جواب نداد، از `nova_working_configs.txt` چند گزینه بعدی را امتحان کن.",
        "",
        "## بهترین گزینه",
        "",
    ]
    if best:
        r = _asdict(best)
        report += [
            f"- Endpoint: `{r.get('endpoint','')}`",
            f"- Latency: `{r.get('latency_ms','-')} ms`",
            f"- Score: `{r.get('score','-')}`",
            f"- Message: `{r.get('message','')}`",
            "",
            "```text",
            best_link,
            "```",
        ]
    else:
        report.append("هیچ کانفیگ سالمی پیدا نشد. از بخش Deploy مطمئن شو Worker بالا آمده، بعد دوباره Nova Easy Mode را اجرا کن.")
    files["nova_report"].write_text("\n".join(report) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in files.items()}
