# -*- coding: utf-8 -*-
"""
BPB Easy Active Config MAIN v9 - core utilities

Stdlib-only helpers for legitimate use with the user's own BPB / Cloudflare deployment.
It fetches a BPB subscription, parses share links, optionally replaces the network endpoint
with user-provided Cloudflare/Clean-IP endpoints, and runs lightweight TCP/TLS/WebSocket checks.

This is not an embedded xray/sing-box core. Final validation should be done in a real client.
"""
from __future__ import annotations

import base64
import concurrent.futures
import ipaddress
import json
import random
import re
import socket
import ssl
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

APP_USER_AGENT = "BPB-Easy-Active-Config-MAIN/9.0"
TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

# Published Cloudflare IPv4 ranges snapshot. Used only for optional random candidate generation.
CF_IPV4_RANGES = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
]



# Cloudflare Worker/Pages commonly available ports. Used by the built-in lightweight scanner.
HTTP_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]
ALL_CF_WORKER_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 80, 8080, 8880, 2052, 2082, 2086, 2095]

@dataclass
class EndpointScanResult:
    ok: bool
    score: int
    latency_ms: int
    endpoint: str
    host: str
    port: int
    protocol: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def endpoints_from_cidrs(text: str, limit_per_cidr: int = 256, total_limit: int = 5000) -> List[str]:
    """Expand small/custom CIDR ranges into IP candidates with a conservative cap."""
    out: List[str] = []
    seen = set()
    limit_per_cidr = max(1, min(int(limit_per_cidr or 256), 2048))
    total_limit = max(1, min(int(total_limit or 5000), 10000))
    for raw in (text or '').replace(',', '\n').splitlines():
        item = raw.strip()
        if not item or item.startswith('#'):
            continue
        try:
            net = ipaddress.ip_network(item, strict=False)
        except Exception:
            continue
        count = 0
        iterator = net.hosts() if net.version == 4 and net.num_addresses > 2 else iter(net)
        for ip in iterator:
            val = str(ip)
            if val not in seen:
                seen.add(val)
                out.append(val)
                count += 1
                if len(out) >= total_limit or count >= limit_per_cidr:
                    break
        if len(out) >= total_limit:
            break
    return out


def expand_scan_endpoints(ip_text: str = '', cidr_text: str = '', random_count: int = 0, ports: Sequence[int] = (443,), limit: int = 5000) -> List[str]:
    """Build endpoint candidates from manual IPs, CIDRs and optional random Cloudflare IPs."""
    base: List[str] = []
    base.extend(normalize_ip_list(ip_text or ''))
    base.extend(endpoints_from_cidrs(cidr_text or '', total_limit=limit))
    if int(random_count or 0) > 0:
        base.extend(random_cloudflare_ips(min(int(random_count or 0), limit)))
    ports = [int(p) for p in ports if str(p).isdigit()] or [443]
    out: List[str] = []
    seen = set()
    for ep in base:
        ep = (ep or '').strip()
        if not ep:
            continue
        has_port = False
        try:
            right = ep.rsplit(':', 1)[1]
            has_port = right.isdigit()
        except Exception:
            has_port = False
        candidates = [ep] if has_port else [f'{ep}:{p}' for p in ports]
        for c in candidates:
            if c not in seen:
                seen.add(c)
                out.append(c)
                if len(out) >= max(1, int(limit or 5000)):
                    return out
    return out


def _http_endpoint_probe(host: str, port: int, sni_host: str, timeout: int) -> Tuple[bool, int, str]:
    start = time.time()
    sock = None
    try:
        sock = socket.create_connection((host, int(port)), timeout=max(1, int(timeout)))
        sock.settimeout(max(1, int(timeout)))
        req = (
            f'GET /cdn-cgi/trace HTTP/1.1\r\n'
            f'Host: {sni_host}\r\n'
            f'User-Agent: {APP_USER_AGENT}\r\n'
            f'Connection: close\r\n\r\n'
        )
        sock.sendall(req.encode('utf-8'))
        resp = sock.recv(512).decode('utf-8', errors='ignore')
        latency = int((time.time() - start) * 1000)
        first = resp.splitlines()[0] if resp.splitlines() else 'empty response'
        ok = first.startswith('HTTP/')
        return ok, latency, first if ok else 'No HTTP response'
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, str(e)[:160]
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def _tls_endpoint_probe(host: str, port: int, sni_host: str, timeout: int) -> Tuple[bool, int, str]:
    start = time.time()
    sock = None
    try:
        raw_sock = socket.create_connection((host, int(port)), timeout=max(1, int(timeout)))
        context = ssl.create_default_context()
        sock = context.wrap_socket(raw_sock, server_hostname=sni_host)
        sock.settimeout(max(1, int(timeout)))
        cert = sock.getpeercert()
        latency = int((time.time() - start) * 1000)
        return bool(cert), latency, 'TLS OK' if cert else 'TLS connected'
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, str(e)[:160]
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def scan_endpoint(endpoint: str, sni_host: str = 'speed.cloudflare.com', timeout: int = 5) -> EndpointScanResult:
    host, port = _parse_endpoint(endpoint, 443)
    proto = 'tls' if int(port) in TLS_PORTS else 'http'
    if proto == 'tls':
        ok, latency, msg = _tls_endpoint_probe(host, int(port), sni_host or 'speed.cloudflare.com', timeout)
    else:
        ok, latency, msg = _http_endpoint_probe(host, int(port), sni_host or 'speed.cloudflare.com', timeout)
    score = 0
    if ok:
        score += 60
    if latency < 250:
        score += 35
    elif latency < 500:
        score += 28
    elif latency < 1000:
        score += 20
    elif latency < 2000:
        score += 10
    return EndpointScanResult(ok, score, latency, f'{host}:{port}', host, int(port), proto, msg)


def scan_endpoints(endpoints: Sequence[str], timeout: int = 5, workers: int = 48, limit: int = 5000, sni_host: str = 'speed.cloudflare.com', progress=None) -> List[EndpointScanResult]:
    items = list(dict.fromkeys([e.strip() for e in endpoints if e and e.strip()]))[:max(1, min(int(limit or 5000), 10000))]
    total = len(items)
    results: List[EndpointScanResult] = []
    workers = max(1, min(int(workers or 48), 120))
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(scan_endpoint, ep, sni_host, timeout): ep for ep in items}
        for fut in concurrent.futures.as_completed(futs):
            done += 1
            try:
                res = fut.result()
            except Exception as e:
                ep = futs[fut]
                host, port = _parse_endpoint(ep, 443)
                res = EndpointScanResult(False, 0, 999999, f'{host}:{port}', host, int(port), 'unknown', str(e)[:160])
            results.append(res)
            if progress:
                progress(done, total, res)
    results.sort(key=lambda r: (not r.ok, -r.score, r.latency_ms))
    return results


def save_ip_scan_outputs(root: Path, endpoints: Sequence[str], results: Sequence[EndpointScanResult]) -> Dict[str, str]:
    out_dir = root / 'output'
    out_dir.mkdir(exist_ok=True)
    clean = [r.endpoint for r in results if r.ok]
    files = {
        'candidates': out_dir / 'ip_candidates.txt',
        'clean': out_dir / 'clean_ips.txt',
        'results': out_dir / 'ip_scan_results.json',
        'report': out_dir / 'ip_scan_report_FA.txt',
    }
    files['candidates'].write_text('\n'.join(endpoints) + ('\n' if endpoints else ''), encoding='utf-8')
    files['clean'].write_text('\n'.join(clean) + ('\n' if clean else ''), encoding='utf-8')
    files['results'].write_text(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [
        'گزارش اسکن IP - BPB Easy Active Config MAIN v9',
        '=' * 48,
        f'کاندیدها: {len(endpoints)}',
        f'IP/Endpoint سالم: {len(clean)}',
        '',
        'بهترین‌ها:',
    ]
    for r in results[:30]:
        lines.append(f"{'OK' if r.ok else 'FAIL'} | {r.endpoint} | {r.latency_ms}ms | {r.message}")
    files['report'].write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {k: str(v) for k, v in files.items()}


@dataclass
class ParsedConfig:
    raw: str
    scheme: str
    host: str
    port: int
    security: str
    network: str
    path: str
    sni: str
    ws_host: str
    user_id: str
    fragment: str
    display_name: str

@dataclass
class ScanResult:
    ok: bool
    score: int
    latency_ms: int
    endpoint: str
    config: str
    message: str
    config_name: str
    scheme: str

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_url_text(url: str, timeout: int = 18) -> str:
    url = (url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("لینک Subscription باید با http:// یا https:// شروع شود.")
    req = Request(url, headers={"User-Agent": APP_USER_AGENT, "Accept": "text/plain,*/*"})
    with urlopen(req, timeout=timeout) as response:
        data = response.read()
    return data.decode("utf-8", errors="ignore")


def maybe_decode_subscription(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    compact = "".join(raw.split())
    try:
        padded = compact + "=" * (-len(compact) % 4)
        decoded = base64.b64decode(padded, validate=False).decode("utf-8", errors="ignore")
        if any(x in decoded for x in ("vless://", "trojan://", "vmess://", "wireguard://", "ss://")):
            return decoded
    except Exception:
        pass
    return text


def split_subscription_lines(text: str) -> List[str]:
    decoded = maybe_decode_subscription(text)
    out: List[str] = []
    for line in decoded.replace("\r", "\n").split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def _qdict(query: str) -> Dict[str, List[str]]:
    q: Dict[str, List[str]] = {}
    for k, v in parse_qsl(query, keep_blank_values=True):
        q.setdefault(k, []).append(v)
    return q


def _qget(q: Dict[str, List[str]], key: str, default: str = "") -> str:
    vals = q.get(key)
    return vals[0] if vals else default


def _b64url_decode(s: str) -> str:
    s = s.strip()
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode()).decode("utf-8", errors="ignore")


def _b64url_encode(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode().rstrip("=")


def parse_share_link(raw: str) -> Optional[ParsedConfig]:
    raw = (raw or "").strip()
    if not raw or "://" not in raw:
        return None
    p = urlparse(raw)
    scheme = p.scheme.lower()

    if scheme in {"vless", "trojan"}:
        if not p.hostname:
            return None
        q = _qdict(p.query)
        security = _qget(q, "security", "tls" if (p.port or 0) in TLS_PORTS else "")
        network = _qget(q, "type", _qget(q, "network", "tcp")) or "tcp"
        port = int(p.port or (443 if security in {"tls", "reality"} else 80))
        path = _qget(q, "path", "/") or "/"
        sni = _qget(q, "sni", _qget(q, "peer", p.hostname)) or p.hostname
        ws_host = _qget(q, "host", sni) or sni
        display = p.fragment or f"{scheme.upper()} {p.hostname}:{port}"
        return ParsedConfig(raw, scheme, p.hostname, port, security, network, path, sni, ws_host, p.username or "", p.fragment, display)

    if scheme == "vmess":
        try:
            payload = _b64url_decode(raw.split("://", 1)[1])
            data = json.loads(payload)
            host = str(data.get("add") or "").strip()
            if not host:
                return None
            port = int(data.get("port") or 443)
            network = str(data.get("net") or data.get("type") or "tcp")
            security = "tls" if str(data.get("tls") or "").lower() == "tls" or port in TLS_PORTS else ""
            path = str(data.get("path") or "/")
            sni = str(data.get("sni") or data.get("host") or host)
            ws_host = str(data.get("host") or sni)
            ps = str(data.get("ps") or f"VMESS {host}:{port}")
            return ParsedConfig(raw, scheme, host, port, security, network, path, sni, ws_host, str(data.get("id") or ""), ps, ps)
        except Exception:
            return None

    # WireGuard/WARP configs are kept in subscription outputs but are not deeply modified/tested here.
    return None


def parse_configs(lines: Sequence[str]) -> List[ParsedConfig]:
    configs: List[ParsedConfig] = []
    seen = set()
    for line in lines:
        cfg = parse_share_link(line)
        if cfg and cfg.raw not in seen:
            configs.append(cfg)
            seen.add(cfg.raw)
    return configs


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except Exception:
        return False


def _parse_endpoint(endpoint: str, default_port: int) -> Tuple[str, int]:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        raise ValueError("endpoint خالی است")
    if "://" in endpoint:
        p = urlparse(endpoint)
        if not p.hostname:
            raise ValueError(f"endpoint نامعتبر: {endpoint}")
        return p.hostname, int(p.port or default_port)
    p = urlparse("//" + endpoint)
    if p.hostname:
        return p.hostname, int(p.port or default_port)
    return endpoint, int(default_port)


def _host_for_netloc(host: str) -> str:
    h = host.strip("[]")
    try:
        ip = ipaddress.ip_address(h)
        return f"[{ip.compressed}]" if ip.version == 6 else ip.compressed
    except Exception:
        return h


def normalize_ip_list(text: str) -> List[str]:
    """Accept one item per line, IP:port, URL, CSV, or plain text containing IPs."""
    out: List[str] = []
    seen = set()
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # CSV first field support.
        if "," in line:
            line = line.split(",", 1)[0].strip()
        # Keep URL/IP:port as-is when parseable; otherwise extract IPv4.
        candidates = [line]
        if not (":" in line or "://" in line):
            candidates = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line) or [line]
        for c in candidates:
            c = c.strip()
            if not c or c in seen:
                continue
            out.append(c)
            seen.add(c)
    return out


def random_cloudflare_ips(count: int) -> List[str]:
    count = max(0, min(int(count or 0), 5000))
    nets = [ipaddress.ip_network(x) for x in CF_IPV4_RANGES]
    results: List[str] = []
    seen = set()
    while len(results) < count:
        net = random.choice(nets)
        # Avoid network/broadcast by staying inside usable range where possible.
        if net.num_addresses <= 4:
            offset = random.randrange(0, net.num_addresses)
        else:
            offset = random.randrange(1, net.num_addresses - 1)
        ip = str(net.network_address + offset)
        if ip not in seen:
            seen.add(ip)
            results.append(ip)
    return results


def _replace_vless_trojan(raw_config: str, endpoint: str) -> str:
    p = urlparse(raw_config.strip())
    cfg = parse_share_link(raw_config)
    if not cfg:
        return raw_config.strip()
    new_host, new_port = _parse_endpoint(endpoint, cfg.port)
    q_items = parse_qsl(p.query, keep_blank_values=True)
    q: Dict[str, str] = dict(q_items)

    # If endpoint becomes a clean IP, preserve the original domain for Cloudflare routing.
    if _is_ip_address(new_host) and cfg.host and not _is_ip_address(cfg.host):
        q.setdefault("sni", cfg.host)
        n = (q.get("type") or q.get("network") or cfg.network or "").lower()
        if n in {"ws", "websocket", "grpc", "xhttp"}:
            q.setdefault("host", cfg.host)

    userinfo = p.netloc.split("@", 1)[0] + "@" if "@" in p.netloc else ""
    netloc = f"{userinfo}{_host_for_netloc(new_host)}:{int(new_port)}"
    query = urlencode(q, doseq=True)
    return urlunparse((p.scheme, netloc, p.path, p.params, query, p.fragment))


def _replace_vmess(raw_config: str, endpoint: str) -> str:
    try:
        data = json.loads(_b64url_decode(raw_config.split("://", 1)[1]))
        old_host = str(data.get("add") or "").strip()
        old_port = int(data.get("port") or 443)
        new_host, new_port = _parse_endpoint(endpoint, old_port)
        data["add"] = new_host
        data["port"] = str(new_port)
        if _is_ip_address(new_host) and old_host and not _is_ip_address(old_host):
            data.setdefault("sni", old_host)
            if str(data.get("net") or "").lower() in {"ws", "grpc", "xhttp"}:
                data.setdefault("host", old_host)
        return "vmess://" + _b64url_encode(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        return raw_config.strip()


def replace_endpoint(raw_config: str, endpoint: str) -> str:
    scheme = urlparse(raw_config.strip()).scheme.lower()
    if scheme in {"vless", "trojan"}:
        return _replace_vless_trojan(raw_config, endpoint)
    if scheme == "vmess":
        return _replace_vmess(raw_config, endpoint)
    return raw_config.strip()


def generate_modified_configs(base_configs: Sequence[str], endpoints: Sequence[str], limit: int = 2000) -> List[str]:
    limit = max(1, min(int(limit or 2000), 20000))
    out: List[str] = []
    seen = set()
    for cfg in base_configs:
        parsed = parse_share_link(cfg)
        if not parsed:
            continue
        for ep in endpoints:
            try:
                mod = replace_endpoint(cfg, ep)
            except Exception:
                continue
            if mod not in seen:
                seen.add(mod)
                out.append(mod)
                if len(out) >= limit:
                    return out
    return out


def tcp_tls_test(cfg: ParsedConfig, timeout: int = 6) -> Tuple[bool, int, str]:
    start = time.time()
    try:
        raw_sock = socket.create_connection((cfg.host, int(cfg.port)), timeout=max(1, int(timeout)))
        if cfg.security in {"tls", "reality"} or cfg.port in TLS_PORTS:
            context = ssl.create_default_context()
            with context.wrap_socket(raw_sock, server_hostname=cfg.sni or cfg.host) as ssock:
                ssock.settimeout(max(1, int(timeout)))
                cert = ssock.getpeercert()
                latency = int((time.time() - start) * 1000)
                return bool(cert or cfg.security == "reality"), latency, "TLS OK" if cert else "TLS connected"
        else:
            raw_sock.close()
            latency = int((time.time() - start) * 1000)
            return True, latency, "TCP OK"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, str(e)[:180]


def websocket_probe(cfg: ParsedConfig, timeout: int = 6) -> Optional[Tuple[bool, int, str]]:
    if (cfg.network or "").lower() not in {"ws", "websocket"}:
        return None
    start = time.time()
    path = cfg.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    key = base64.b64encode(b"bpb-easy-active-v9").decode()
    host_header = cfg.ws_host or cfg.sni or cfg.host
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_header}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"User-Agent: {APP_USER_AGENT}\r\n\r\n"
    )
    sock = None
    try:
        sock = socket.create_connection((cfg.host, int(cfg.port)), timeout=max(1, int(timeout)))
        if cfg.security in {"tls", "reality"} or cfg.port in TLS_PORTS:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=cfg.sni or cfg.host)
        sock.settimeout(max(1, int(timeout)))
        sock.sendall(req.encode("utf-8"))
        resp = sock.recv(768).decode("utf-8", errors="ignore")
        latency = int((time.time() - start) * 1000)
        first = resp.splitlines()[0] if resp.splitlines() else "empty response"
        if "101 Switching Protocols" in resp:
            return True, latency, "WebSocket 101 OK"
        if "HTTP/" in resp:
            return False, latency, f"WS responded but no 101: {first}"
        return False, latency, "No HTTP/WebSocket response"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, str(e)[:180]
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def _uuid_to_bytes(uuid: str) -> Optional[bytes]:
    clean = (uuid or "").strip().replace("-", "").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", clean):
        return None
    return bytes(int(clean[i:i+2], 16) for i in range(0, 32, 2))


def _ws_frame(payload: bytes, opcode: int = 2) -> bytes:
    """Build a masked client-to-server WebSocket frame."""
    payload = payload or b""
    first = 0x80 | (opcode & 0x0F)
    n = len(payload)
    mask_key = random.randbytes(4) if hasattr(random, "randbytes") else bytes(random.getrandbits(8) for _ in range(4))
    if n < 126:
        header = bytes([first, 0x80 | n])
    elif n < 65536:
        header = bytes([first, 0x80 | 126]) + n.to_bytes(2, "big")
    else:
        header = bytes([first, 0x80 | 127]) + n.to_bytes(8, "big")
    masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    return header + mask_key + masked


def _ws_read_frame(sock, timeout: int = 6) -> bytes:
    sock.settimeout(max(1, int(timeout)))
    head = sock.recv(2)
    if len(head) < 2:
        return b""
    b1, b2 = head[0], head[1]
    length = b2 & 0x7F
    if length == 126:
        length = int.from_bytes(sock.recv(2), "big")
    elif length == 127:
        length = int.from_bytes(sock.recv(8), "big")
    masked = bool(b2 & 0x80)
    mask = sock.recv(4) if masked else b""
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    if masked and mask:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return data


def _build_vless_probe_payload(cfg: ParsedConfig) -> Optional[bytes]:
    uid = _uuid_to_bytes(cfg.user_id)
    if not uid:
        return None
    target = b"www.cloudflare.com"
    http = b"GET /cdn-cgi/trace HTTP/1.1\r\nHost: www.cloudflare.com\r\nConnection: close\r\n\r\n"
    # version + uuid + optlen + command TCP + port 80 + domain address + early data
    return bytes([0]) + uid + bytes([0, 1]) + (80).to_bytes(2, "big") + bytes([2, len(target)]) + target + http


def vless_ws_proxy_probe(cfg: ParsedConfig, timeout: int = 6) -> Optional[Tuple[bool, int, str]]:
    """Validate VLESS-over-WebSocket more deeply by doing a real WS upgrade and a tiny VLESS TCP request.

    This is still a lightweight validation, but it is stronger than only TCP/TLS ping because it checks:
    1) TLS/socket reachability, 2) correct WS path/host, 3) UUID acceptance, 4) remote TCP response.
    """
    if cfg.scheme != "vless" or (cfg.network or "").lower() not in {"ws", "websocket"}:
        return None
    probe_payload = _build_vless_probe_payload(cfg)
    if not probe_payload:
        return None
    start = time.time()
    path = cfg.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    key = base64.b64encode(random.randbytes(16) if hasattr(random, "randbytes") else bytes(random.getrandbits(8) for _ in range(16))).decode()
    host_header = cfg.ws_host or cfg.sni or cfg.host
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_header}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"User-Agent: {APP_USER_AGENT}\r\n\r\n"
    )
    sock = None
    try:
        raw = socket.create_connection((cfg.host, int(cfg.port)), timeout=max(1, int(timeout)))
        if cfg.security in {"tls", "reality"} or cfg.port in TLS_PORTS:
            context = ssl.create_default_context()
            sock = context.wrap_socket(raw, server_hostname=cfg.sni or cfg.host)
        else:
            sock = raw
        sock.settimeout(max(1, int(timeout)))
        sock.sendall(req.encode("utf-8"))
        resp = b""
        while b"\r\n\r\n" not in resp and len(resp) < 4096:
            part = sock.recv(1024)
            if not part:
                break
            resp += part
        first = resp.decode("utf-8", errors="ignore").splitlines()[0] if resp else "empty response"
        if b" 101 " not in resp and b"101 Switching Protocols" not in resp:
            latency = int((time.time() - start) * 1000)
            return False, latency, f"WS upgrade failed: {first}"
        sock.sendall(_ws_frame(probe_payload, opcode=2))
        data = _ws_read_frame(sock, timeout=timeout)
        latency = int((time.time() - start) * 1000)
        if len(data) >= 2:
            body = data[2:]
            if b"HTTP/" in body or b"colo=" in body or len(body) > 12:
                return True, latency, "VLESS WS proxy OK"
        return False, latency, "WS upgraded but VLESS probe had no useful response"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, str(e)[:180]
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def score_result(tcp_ok: bool, tcp_latency: int, ws_result: Optional[Tuple[bool, int, str]]) -> int:
    score = 0
    if tcp_ok:
        score += 50
    if tcp_latency < 350:
        score += 35
    elif tcp_latency < 800:
        score += 25
    elif tcp_latency < 1600:
        score += 15
    elif tcp_latency < 3000:
        score += 7
    if ws_result:
        ws_ok, ws_latency, _ = ws_result
        if ws_ok:
            score += 35
        if ws_latency < tcp_latency + 500:
            score += 10
    return score


def test_one(raw_config: str, timeout: int = 6) -> ScanResult:
    cfg = parse_share_link(raw_config)
    if not cfg:
        return ScanResult(False, 0, 999999, "-", raw_config, "Unsupported or invalid config", "Invalid", "-")
    endpoint = f"{cfg.host}:{cfg.port}"

    actual_vless = vless_ws_proxy_probe(cfg, timeout=timeout)
    if actual_vless is not None:
        ok, latency, msg = actual_vless
        score = (95 if ok else 0)
        if ok:
            if latency < 350:
                score += 35
            elif latency < 800:
                score += 25
            elif latency < 1600:
                score += 15
            elif latency < 3000:
                score += 7
        return ScanResult(ok, score, latency, endpoint, raw_config, msg, cfg.display_name, cfg.scheme)

    tcp_ok, tcp_latency, tcp_msg = tcp_tls_test(cfg, timeout=timeout)
    ws = websocket_probe(cfg, timeout=timeout)
    score = score_result(tcp_ok, tcp_latency, ws)
    msg = tcp_msg
    if ws:
        msg += " | " + ws[2]
    ok = tcp_ok and (ws[0] if ws else True)
    return ScanResult(ok, score, tcp_latency, endpoint, raw_config, msg, cfg.display_name, cfg.scheme)


def test_configs(configs: Sequence[str], timeout: int = 6, workers: int = 24, limit: int = 2000, progress=None) -> List[ScanResult]:
    items = list(dict.fromkeys([c.strip() for c in configs if c and c.strip()]))[:max(1, int(limit or 2000))]
    total = len(items)
    results: List[ScanResult] = []
    workers = max(1, min(int(workers or 24), 80))
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        future_map = {ex.submit(test_one, cfg, timeout): cfg for cfg in items}
        for fut in concurrent.futures.as_completed(future_map):
            done += 1
            try:
                res = fut.result()
            except Exception as e:
                cfg = future_map[fut]
                res = ScanResult(False, 0, 999999, "-", cfg, str(e)[:180], "Error", "-")
            results.append(res)
            if progress:
                progress(done, total, res)
    results.sort(key=lambda r: (not r.ok, -r.score, r.latency_ms))
    return results


def choose_best(results: Sequence[ScanResult]) -> Optional[ScanResult]:
    for r in results:
        if r.ok:
            return r
    return results[0] if results else None


def save_outputs(root: Path, base_configs: Sequence[str], generated_configs: Sequence[str], results: Sequence[ScanResult], best: Optional[ScanResult]) -> Dict[str, str]:
    out_dir = root / "output"
    out_dir.mkdir(exist_ok=True)
    files = {
        "base": out_dir / "base_configs.txt",
        "generated": out_dir / "generated_configs.txt",
        "results": out_dir / "scan_results.json",
        "best": out_dir / "best_active_config.txt",
        "working": out_dir / "working_configs.txt",
        "top": out_dir / "top_active_configs.txt",
        "report": out_dir / "report_FA.txt",
    }
    files["base"].write_text("\n".join(base_configs) + ("\n" if base_configs else ""), encoding="utf-8")
    files["generated"].write_text("\n".join(generated_configs) + ("\n" if generated_configs else ""), encoding="utf-8")
    files["results"].write_text(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
    files["best"].write_text((best.config if best else "") + ("\n" if best else ""), encoding="utf-8")
    working = [r.config for r in results if r.ok]
    files["working"].write_text("\n".join(working) + ("\n" if working else ""), encoding="utf-8")
    files["top"].write_text("\n".join([r.config for r in results[:50] if r.config]) + ("\n" if results else ""), encoding="utf-8")
    report_lines = [
        "گزارش BPB Easy Active Config MAIN v9",
        "=" * 42,
        f"کانفیگ‌های پایه: {len(base_configs)}",
        f"کانفیگ‌های تولیدشده/تست‌شده: {len(generated_configs)}",
        f"نتایج تست: {len(results)}",
        "",
    ]
    if best:
        report_lines += [
            "بهترین کانفیگ پیشنهادی:",
            best.config,
            "",
            f"Endpoint: {best.endpoint}",
            f"Latency: {best.latency_ms} ms",
            f"Score: {best.score}",
            f"Message: {best.message}",
        ]
    else:
        report_lines.append("هیچ کانفیگی برای خروجی انتخاب نشد.")
    files["report"].write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return {k: str(v) for k, v in files.items()}
