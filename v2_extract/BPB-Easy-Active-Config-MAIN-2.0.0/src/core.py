# -*- coding: utf-8 -*-
"""
BPB/Nova Easy Active Config v2 - core utilities

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
from urllib.error import HTTPError, URLError

APP_USER_AGENT = "BPB-Nova-Easy-Active-Config/2.0"
TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

# Published Cloudflare IPv4 ranges snapshot. Used only for optional random candidate generation.
CF_IPV4_RANGES = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
]

# SNI rotation list for scanner - Cloudflare domains
SNI_ROTATION_LIST = [
    "speed.cloudflare.com",
    "www.cloudflare.com",
    "cloudflare.com",
    "1.1.1.1.cdn.cloudflare.net",
    "blog.cloudflare.com",
]

# Cloudflare Worker/Pages commonly available ports. Used by the built-in lightweight scanner.
HTTP_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]
ALL_CF_WORKER_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 80, 8080, 8880, 2052, 2082, 2086, 2095]

# Minimum score threshold for a config to be included in working_configs.txt
WORKING_CONFIG_MIN_SCORE = 50

# Download speed test URL
SPEED_TEST_URL = "https://speed.cloudflare.com/__down?bytes=65536"


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
    download_speed_kbps: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _rotate_sni(index: int = 0) -> str:
    """Return an SNI hostname rotated from the SNI_ROTATION_LIST."""
    return SNI_ROTATION_LIST[index % len(SNI_ROTATION_LIST)]


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


# ---------------------------------------------------------------------------
# Phase 1 probes: Quick TCP/TLS with timeout budget splitting
# ---------------------------------------------------------------------------

def _tcp_probe(host: str, port: int, timeout: float) -> Tuple[bool, int, str]:
    """TCP connection probe. Returns (ok, latency_ms, message)."""
    start = time.time()
    sock = None
    try:
        sock = socket.create_connection((host, int(port)), timeout=max(0.5, timeout))
        latency = int((time.time() - start) * 1000)
        return True, latency, "TCP OK"
    except socket.timeout:
        latency = int((time.time() - start) * 1000)
        return False, latency, "TCP timeout"
    except (ConnectionRefusedError, OSError) as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"TCP refused: {str(e)[:80]}"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"TCP error: {str(e)[:80]}"
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def _tls_probe(host: str, port: int, sni_host: str, timeout: float) -> Tuple[bool, int, str]:
    """TLS handshake probe. Returns (ok, latency_ms, message)."""
    start = time.time()
    sock = None
    raw_sock = None
    try:
        raw_sock = socket.create_connection((host, int(port)), timeout=max(0.5, timeout))
        context = ssl.create_default_context()
        sock = context.wrap_socket(raw_sock, server_hostname=sni_host)
        sock.settimeout(max(0.5, timeout))
        cert = sock.getpeercert()
        latency = int((time.time() - start) * 1000)
        # Extract Cloudflare colo from cert if present
        colo = ""
        if cert:
            for subj in cert.get("subject", ()):
                for k, v in subj:
                    if k == "commonName" and "cloudflare" in v.lower():
                        colo = v
        msg = "TLS OK"
        if colo:
            msg = f"TLS OK (CF cert: {colo})"
        return bool(cert), latency, msg
    except ssl.SSLCertVerificationError as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"TLS cert error: {str(e)[:80]}"
    except socket.timeout:
        latency = int((time.time() - start) * 1000)
        return False, latency, "TLS timeout"
    except (ConnectionRefusedError, OSError) as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"TLS refused: {str(e)[:80]}"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"TLS error: {str(e)[:80]}"
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        try:
            if raw_sock and raw_sock != sock:
                raw_sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase 2 probes: HTTP + WebSocket DPI detection
# ---------------------------------------------------------------------------

def _http_probe(host: str, port: int, sni_host: str, timeout: float) -> Tuple[bool, int, str]:
    """HTTP probe that checks for Cloudflare colo in response. Returns (ok, latency_ms, message)."""
    start = time.time()
    sock = None
    try:
        if int(port) in TLS_PORTS:
            raw_sock = socket.create_connection((host, int(port)), timeout=max(0.5, timeout))
            context = ssl.create_default_context()
            sock = context.wrap_socket(raw_sock, server_hostname=sni_host)
        else:
            sock = socket.create_connection((host, int(port)), timeout=max(0.5, timeout))
        sock.settimeout(max(0.5, timeout))
        req = (
            f'GET /cdn-cgi/trace HTTP/1.1\r\n'
            f'Host: {sni_host}\r\n'
            f'User-Agent: {APP_USER_AGENT}\r\n'
            f'Connection: close\r\n\r\n'
        )
        sock.sendall(req.encode('utf-8'))
        resp = b""
        while b"\r\n\r\n" not in resp and len(resp) < 4096:
            try:
                chunk = sock.recv(2048)
                if not chunk:
                    break
                resp += chunk
            except socket.timeout:
                break
        latency = int((time.time() - start) * 1000)
        resp_text = resp.decode('utf-8', errors='ignore')
        first_line = resp_text.splitlines()[0] if resp_text.splitlines() else 'empty response'
        if not first_line.startswith('HTTP/'):
            return False, latency, 'No HTTP response'
        # Check for 2xx status
        status_match = re.match(r'HTTP/\S+\s+(\d+)', first_line)
        if not status_match:
            return False, latency, f'Bad HTTP response: {first_line[:60]}'
        status_code = int(status_match.group(1))
        # Check for Cloudflare colo in body
        colo = ""
        if b"colo=" in resp:
            for line in resp_text.splitlines():
                if line.strip().startswith("colo="):
                    colo = line.strip().split("=", 1)[1].strip()
                    break
        if 200 <= status_code < 300:
            msg = f"HTTP {status_code} OK"
            if colo:
                msg = f"HTTP {status_code} OK (colo={colo})"
            return True, latency, msg
        return False, latency, f"HTTP {status_code}"
    except socket.timeout:
        latency = int((time.time() - start) * 1000)
        return False, latency, "HTTP timeout"
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return False, latency, f"HTTP error: {str(e)[:80]}"
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def scan_endpoint_dpi(host: str, port: int, sni_host: str, timeout: float) -> Tuple[bool, str]:
    """Two-stage DPI detection test.

    Stage 1: Establish TLS connection and hold IDLE for 2 seconds.
             If the connection gets RST/EOF (not timeout), DPI is detected - endpoint is bad.
    Stage 2: Send a WebSocket upgrade request. If the server responds with HTTP,
             WS traffic is not being blocked by DPI.

    Returns (dpi_pass, message).
    """
    sock = None
    raw_sock = None
    try:
        # Stage 1: TLS idle hold test
        if int(port) in TLS_PORTS:
            try:
                raw_sock = socket.create_connection((host, int(port)), timeout=max(2, timeout))
                context = ssl.create_default_context()
                sock = context.wrap_socket(raw_sock, server_hostname=sni_host)
                raw_sock = None  # ownership transferred
                sock.settimeout(2.5)
                # Hold the connection idle for 2 seconds
                time.sleep(2.0)
                # Try a non-blocking read - if we get RST/EOF immediately, DPI detected
                try:
                    peek = sock.recv(1, socket.MSG_PEEK)
                    if peek == b'':
                        # Connection was closed (EOF) - likely DPI
                        return False, "DPI detected: connection closed during idle hold"
                except socket.timeout:
                    # Timeout is GOOD - means the connection survived the idle period
                    pass
                except ConnectionResetError:
                    # RST during idle - DPI detected
                    return False, "DPI detected: RST during idle hold"
                except (ConnectionAbortedError, OSError):
                    # Connection was killed - possible DPI
                    return False, "DPI detected: connection aborted during idle hold"
                except ssl.SSLError:
                    # SSL error during idle - possible DPI
                    return False, "DPI detected: SSL error during idle hold"
            except socket.timeout:
                return False, "DPI test: TLS connection timeout"
            except (ConnectionRefusedError, OSError):
                return False, "DPI test: TLS connection refused"
            except ssl.SSLCertVerificationError:
                # Cert error is not DPI, but endpoint is still bad
                return False, "DPI test: TLS cert verification failed"
            except Exception as e:
                return False, f"DPI test: TLS error: {str(e)[:60]}"
        else:
            # Non-TLS port: skip idle hold test, just do WS check
            sock = socket.create_connection((host, int(port)), timeout=max(2, timeout))
            sock.settimeout(max(2, timeout))

        # Stage 2: WebSocket upgrade request
        ws_key = base64.b64encode(b"bpb-dpi-scan-v9-probe").decode()
        ws_req = (
            f'GET / HTTP/1.1\r\n'
            f'Host: {sni_host}\r\n'
            f'Upgrade: websocket\r\n'
            f'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Key: {ws_key}\r\n'
            f'Sec-WebSocket-Version: 13\r\n'
            f'User-Agent: {APP_USER_AGENT}\r\n\r\n'
        )
        try:
            sock.sendall(ws_req.encode('utf-8'))
            resp = b""
            while b"\r\n\r\n" not in resp and len(resp) < 4096:
                try:
                    chunk = sock.recv(2048)
                    if not chunk:
                        break
                    resp += chunk
                except socket.timeout:
                    break
            resp_text = resp.decode('utf-8', errors='ignore')
            if "HTTP/" in resp_text:
                # Server responded with HTTP - WS traffic is not being blocked by DPI
                return True, "WS DPI pass: server responded with HTTP"
            return False, "WS DPI fail: no HTTP response to WS upgrade"
        except ConnectionResetError:
            return False, "WS DPI fail: RST after WS upgrade request"
        except Exception as e:
            return False, f"WS DPI fail: {str(e)[:60]}"
    except Exception as e:
        return False, f"DPI test error: {str(e)[:60]}"
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        try:
            if raw_sock:
                raw_sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase 3: Download speed test
# ---------------------------------------------------------------------------

def _download_speed_test(host: str, port: int, sni_host: str, timeout: float = 10.0) -> Tuple[float, str]:
    """Download speed test by fetching from speed.cloudflare.com/__down?bytes=65536.

    Returns (speed_kbps, message). Speed is 0 if test fails.
    """
    sock = None
    raw_sock = None
    try:
        start = time.time()
        if int(port) in TLS_PORTS:
            raw_sock = socket.create_connection((host, int(port)), timeout=max(2, timeout))
            context = ssl.create_default_context()
            sock = context.wrap_socket(raw_sock, server_hostname=sni_host)
            raw_sock = None
        else:
            sock = socket.create_connection((host, int(port)), timeout=max(2, timeout))
        sock.settimeout(max(2, timeout))

        req = (
            f'GET /__down?bytes=65536 HTTP/1.1\r\n'
            f'Host: speed.cloudflare.com\r\n'
            f'User-Agent: {APP_USER_AGENT}\r\n'
            f'Connection: close\r\n\r\n'
        )
        sock.sendall(req.encode('utf-8'))

        # Read response
        data = b""
        headers_done = False
        while True:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                data += chunk
                if not headers_done and b"\r\n\r\n" in data:
                    headers_done = True
            except socket.timeout:
                break

        elapsed = time.time() - start
        # Separate headers from body
        body = data
        if b"\r\n\r\n" in data:
            body = data.split(b"\r\n\r\n", 1)[1]

        body_size = len(body)
        if elapsed > 0 and body_size > 0:
            speed_kbps = (body_size / elapsed) / 1024.0
            return speed_kbps, f"Speed: {speed_kbps:.1f} KB/s ({body_size} bytes in {elapsed:.2f}s)"
        return 0, "Speed test: no data received"
    except Exception as e:
        return 0, f"Speed test error: {str(e)[:60]}"
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        try:
            if raw_sock:
                raw_sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Neighbor IP expansion
# ---------------------------------------------------------------------------

def expand_neighbor_ips(working_ips: List[str], radius: int = 8, max_per_hit: int = 6, total_max: int = 200) -> List[str]:
    """For each working IP, probe its neighbors (IP +/- offset) to find clusters.

    Args:
        working_ips: List of IP addresses that passed Phase 1.
        radius: How far to look from each working IP (max offset).
        max_per_hit: Maximum neighbors to generate per working IP.
        total_max: Maximum total neighbor IPs to generate.

    Returns:
        List of neighbor IP strings (without ports).
    """
    neighbors: List[str] = []
    seen = set()
    # Track working IPs to avoid duplicates
    for ip_str in working_ips:
        ip_str = ip_str.strip().rsplit(":", 1)[0] if ":" in ip_str and not ip_str.startswith("[") else ip_str.strip()
        seen.add(ip_str)

    for ip_str in working_ips:
        if len(neighbors) >= total_max:
            break
        # Strip port if present
        clean_ip = ip_str.strip()
        if ":" in clean_ip and not clean_ip.startswith("["):
            clean_ip = clean_ip.rsplit(":", 1)[0]
        try:
            ip = ipaddress.ip_address(clean_ip)
        except Exception:
            continue
        if ip.version != 4:
            continue

        count = 0
        offsets = list(range(1, radius + 1))
        random.shuffle(offsets)
        for offset in offsets:
            if count >= max_per_hit or len(neighbors) >= total_max:
                break
            for delta in (offset, -offset):
                if count >= max_per_hit or len(neighbors) >= total_max:
                    break
                try:
                    neighbor = str(ipaddress.ip_address(int(ip) + delta))
                    if neighbor not in seen:
                        seen.add(neighbor)
                        neighbors.append(neighbor)
                        count += 1
                except Exception:
                    continue
    return neighbors


# ---------------------------------------------------------------------------
# Improved scoring function
# ---------------------------------------------------------------------------

def _score_endpoint(tcp_ok: bool, tls_ok: bool, http_ok: bool, ws_dpi_pass: bool,
                    latency_ms: int, download_speed_kbps: float = 0.0) -> int:
    """Score an endpoint based on all test results.

    Scoring:
    - TCP OK: +20
    - TLS OK: +25
    - HTTP OK (2xx + Cloudflare colo): +30
    - WebSocket DPI pass: +20
    - Latency < 200ms: +25, < 500ms: +15, < 1000ms: +10
    - Download speed > 5MB/s: +15, > 1MB/s: +10
    """
    score = 0
    if tcp_ok:
        score += 20
    if tls_ok:
        score += 25
    if http_ok:
        score += 30
    if ws_dpi_pass:
        score += 20
    # Latency scoring
    if latency_ms < 200:
        score += 25
    elif latency_ms < 500:
        score += 15
    elif latency_ms < 1000:
        score += 10
    # Download speed scoring
    if download_speed_kbps > 5120:  # > 5 MB/s
        score += 15
    elif download_speed_kbps > 1024:  # > 1 MB/s
        score += 10
    return score


# ---------------------------------------------------------------------------
# Multi-phase scan
# ---------------------------------------------------------------------------

def scan_endpoint(endpoint: str, sni_host: str = 'speed.cloudflare.com', timeout: int = 5) -> EndpointScanResult:
    """Single endpoint scan with improved scoring (backward compatible)."""
    host, port = _parse_endpoint(endpoint, 443)
    proto = 'tls' if int(port) in TLS_PORTS else 'http'

    # Timeout budget splitting: TCP=1/4, TLS=1/2, HTTP=1/4
    tcp_timeout = max(1, timeout / 4.0)
    tls_timeout = max(1, timeout / 2.0)
    http_timeout = max(1, timeout / 4.0)

    # Use rotated SNI
    sni = sni_host or 'speed.cloudflare.com'

    tcp_ok = False
    tls_ok = False
    http_ok = False
    ws_dpi_pass = False
    latency_ms = 999999
    messages = []

    # TCP probe
    tcp_ok, tcp_lat, tcp_msg = _tcp_probe(host, port, tcp_timeout)
    messages.append(tcp_msg)
    if tcp_ok:
        latency_ms = tcp_lat

    # TLS probe (for TLS ports)
    if int(port) in TLS_PORTS:
        tls_ok, tls_lat, tls_msg = _tls_probe(host, port, sni, tls_timeout)
        messages.append(tls_msg)
        if tls_ok and tls_lat < latency_ms:
            latency_ms = tls_lat
        if not tls_ok:
            # If TLS fails, endpoint is likely bad
            score = _score_endpoint(tcp_ok, tls_ok, http_ok, ws_dpi_pass, latency_ms)
            return EndpointScanResult(False, score, latency_ms, f'{host}:{port}', host, int(port), proto, " | ".join(messages))

    if not tcp_ok and not tls_ok:
        score = _score_endpoint(tcp_ok, tls_ok, http_ok, ws_dpi_pass, latency_ms)
        return EndpointScanResult(False, score, latency_ms, f'{host}:{port}', host, int(port), proto, " | ".join(messages))

    # HTTP probe
    http_ok, http_lat, http_msg = _http_probe(host, port, sni, http_timeout)
    messages.append(http_msg)
    if http_ok and http_lat < latency_ms:
        latency_ms = http_lat

    ok = (tcp_ok or tls_ok) and (http_ok or tls_ok)
    score = _score_endpoint(tcp_ok, tls_ok, http_ok, ws_dpi_pass, latency_ms)
    return EndpointScanResult(ok, score, latency_ms, f'{host}:{port}', host, int(port), proto, " | ".join(messages))


def scan_endpoints(endpoints: Sequence[str], timeout: int = 5, workers: int = 48, limit: int = 5000,
                   sni_host: str = 'speed.cloudflare.com', progress=None) -> List[EndpointScanResult]:
    """Multi-phase scan based on SenPaiScanner methodology.

    Phase 1: Quick probe all candidates with TCP/TLS
    Phase 2: For candidates that pass Phase 1, do HTTP + WebSocket DPI test
    Phase 3: For top 20, do download speed test
    """
    items = list(dict.fromkeys([e.strip() for e in endpoints if e and e.strip()]))[:max(1, min(int(limit or 5000), 10000))]
    total = len(items)
    results: List[EndpointScanResult] = []
    workers = max(1, min(int(workers or 48), 120))

    # --- Phase 1: Quick TCP/TLS probe ---
    phase1_results: List[EndpointScanResult] = []
    done = 0

    # Timeout budget splitting: TCP=1/4, TLS=1/2
    tcp_timeout = max(1, timeout / 4.0)
    tls_timeout = max(1, timeout / 2.0)

    def _phase1_probe(endpoint: str) -> EndpointScanResult:
        host, port = _parse_endpoint(endpoint, 443)
        proto = 'tls' if int(port) in TLS_PORTS else 'http'
        # Rotate SNI based on index
        sni = sni_host or 'speed.cloudflare.com'

        tcp_ok = False
        tls_ok = False
        latency_ms = 999999
        messages = []

        tcp_ok, tcp_lat, tcp_msg = _tcp_probe(host, port, tcp_timeout)
        messages.append(tcp_msg)
        if tcp_ok:
            latency_ms = tcp_lat

        if int(port) in TLS_PORTS:
            tls_ok, tls_lat, tls_msg = _tls_probe(host, port, sni, tls_timeout)
            messages.append(tls_msg)
            if tls_ok and tls_lat < latency_ms:
                latency_ms = tls_lat

        passed = tcp_ok or tls_ok
        score = _score_endpoint(tcp_ok, tls_ok, False, False, latency_ms)
        return EndpointScanResult(passed, score, latency_ms, f'{host}:{port}', host, int(port), proto, " | ".join(messages))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_phase1_probe, ep): ep for ep in items}
        for fut in concurrent.futures.as_completed(futs):
            done += 1
            try:
                res = fut.result()
            except Exception as e:
                ep = futs[fut]
                host, port = _parse_endpoint(ep, 443)
                res = EndpointScanResult(False, 0, 999999, f'{host}:{port}', host, int(port), 'unknown', str(e)[:160])
            phase1_results.append(res)
            if progress:
                progress(done, total, res)

    # Sort Phase 1 results
    phase1_results.sort(key=lambda r: (not r.ok, -r.score, r.latency_ms))

    # --- Phase 2: HTTP + WebSocket DPI test for passing candidates ---
    passing = [r for r in phase1_results if r.ok]
    if passing:
        phase2_map: Dict[str, EndpointScanResult] = {r.endpoint: r for r in phase1_results}
        done_p2 = 0
        total_p2 = len(passing)

        def _phase2_probe(r: EndpointScanResult) -> EndpointScanResult:
            host, port = r.host, r.port
            sni = sni_host or 'speed.cloudflare.com'
            http_timeout = max(1, timeout / 4.0)

            http_ok, http_lat, http_msg = _http_probe(host, port, sni, http_timeout)
            ws_dpi_pass, ws_msg = scan_endpoint_dpi(host, port, sni, timeout=max(2, timeout / 2.0))

            latency_ms = r.latency_ms
            if http_ok and http_lat < latency_ms:
                latency_ms = http_lat

            messages = [r.message, http_msg, ws_msg]
            ok = r.ok and (http_ok or r.port in TLS_PORTS)
            score = _score_endpoint(True, r.port in TLS_PORTS, http_ok, ws_dpi_pass, latency_ms)
            return EndpointScanResult(ok, score, latency_ms, r.endpoint, r.host, r.port, r.protocol, " | ".join(messages))

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs2 = {ex.submit(_phase2_probe, r): r for r in passing}
            for fut in concurrent.futures.as_completed(futs2):
                done_p2 += 1
                try:
                    res = fut.result()
                    phase2_map[res.endpoint] = res
                except Exception:
                    pass

        # Rebuild results from phase2_map
        results = list(phase2_map.values())
        results.sort(key=lambda r: (not r.ok, -r.score, r.latency_ms))
    else:
        results = phase1_results

    # --- Phase 3: Download speed test for top 20 ---
    top_candidates = [r for r in results if r.ok][:20]
    if top_candidates:
        speed_map: Dict[str, float] = {}

        def _phase3_probe(r: EndpointScanResult) -> Tuple[str, float, str]:
            sni = sni_host or 'speed.cloudflare.com'
            speed, msg = _download_speed_test(r.host, r.port, sni, timeout=max(5, timeout * 2))
            return r.endpoint, speed, msg

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, 10)) as ex:
            futs3 = {ex.submit(_phase3_probe, r): r for r in top_candidates}
            for fut in concurrent.futures.as_completed(futs3):
                try:
                    ep, speed, msg = fut.result()
                    speed_map[ep] = speed
                except Exception:
                    pass

        # Update results with speed scores
        for r in results:
            if r.endpoint in speed_map:
                speed = speed_map[r.endpoint]
                r.download_speed_kbps = speed
                # Recalculate score including speed
                has_tls = r.port in TLS_PORTS
                r.score = _score_endpoint(True, has_tls, True, True, r.latency_ms, speed)

        results.sort(key=lambda r: (not r.ok, -r.score, r.latency_ms))

    # --- Neighbor IP expansion ---
    working_ips = [r.host for r in results if r.ok and r.score >= 40]
    if working_ips:
        neighbor_ips = expand_neighbor_ips(working_ips, radius=8, max_per_hit=6, total_max=200)
        if neighbor_ips:
            # Quick probe neighbors
            neighbor_endpoints = [f"{ip}:443" for ip in neighbor_ips]
            neighbor_results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
                futs_n = {ex.submit(_phase1_probe, ep): ep for ep in neighbor_endpoints}
                for fut in concurrent.futures.as_completed(futs_n):
                    try:
                        nr = fut.result()
                        if nr.ok:
                            neighbor_results.append(nr)
                    except Exception:
                        pass

            # Merge neighbor results that aren't duplicates
            existing_endpoints = {r.endpoint for r in results}
            for nr in neighbor_results:
                if nr.endpoint not in existing_endpoints:
                    results.append(nr)
                    existing_endpoints.add(nr.endpoint)

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
        speed_info = f" | speed: {r.download_speed_kbps:.1f}KB/s" if r.download_speed_kbps > 0 else ""
        lines.append(f"{'OK' if r.ok else 'FAIL'} | {r.endpoint} | {r.latency_ms}ms | score: {r.score}{speed_info} | {r.message}")
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


def fetch_url_text(url: str, timeout: int = 18, retries: int = 2) -> tuple:
    """Fetch URL text with retry logic. Returns (text, error_message).

    If successful: (text, None)
    If failed: (error_text, error_detail)
    """
    url = (url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return "", "لینک Subscription باید با http:// یا https:// شروع شود."

    last_error = ""
    for attempt in range(max(1, retries)):
        req = Request(url, headers={"User-Agent": APP_USER_AGENT, "Accept": "text/plain,*/*"})
        try:
            with urlopen(req, timeout=timeout) as response:
                data = response.read()
            return data.decode("utf-8", errors="ignore"), None
        except HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="ignore")[:300]
            except Exception:
                body = ""
            if e.code == 500:
                last_error = f"سرور Worker خطای 500 داده. احتمالاً Worker درست Deploy نشده یا UUID تنظیم نشده."
                if attempt < retries - 1:
                    time.sleep(1.5)
                    continue
            elif e.code == 401:
                return "", f"خطای 401: دسترسی غیرمجاز. Worker نیاز به تنظیمات دارد."
            elif e.code == 404:
                return "", f"خطای 404: مسیر Subscription اشتباه است. مسیر صحیح معمولاً /sub است."
            else:
                last_error = f"خطای HTTP {e.code}: {e.reason}"
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
            return f"[HTTP Error {e.code}: {e.reason}] {body}", last_error
        except URLError as e:
            return "", f"اتصال برقرار نشد: {str(e)[:150]}"
        except socket.timeout:
            last_error = "زمان اتصال به سرور تمام شد. اینترنت خود را چک کن."
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return "", last_error
        except Exception as e:
            return "", f"خطای دریافت: {str(e)[:150]}"
    return "", last_error


def build_bpb_template_configs(worker_url: str, uuid: str, sub_path: str = "sub", proxy_ip: str = "") -> List[str]:
    """Build default BPB VLESS/Trojan configs from worker URL and UUID.

    This is a fallback when the subscription endpoint returns errors.
    It creates standard BPB Worker Panel config patterns.
    """
    configs = []
    uuid = (uuid or "").strip()
    if not uuid:
        return configs

    # Parse worker URL to get the hostname
    worker_url = (worker_url or "").strip()
    if not worker_url:
        return configs

    # Extract hostname from URL - remove /sub or other paths
    parsed = urlparse(worker_url)
    hostname = (parsed.hostname or "").strip()
    if not hostname:
        # Maybe it's just a hostname like bpb-panel.account.workers.dev
        hostname = worker_url.split("/")[0].split(":")[0].strip()
    if not hostname:
        return configs

    # Standard BPB Worker Panel VLESS WS config patterns
    # Pattern 1: VLESS WS TLS (primary - most common BPB config)
    vless_ws_tls = f"vless://{uuid}@{hostname}:443?encryption=none&security=tls&sni={hostname}&type=ws&host={hostname}&path=%2F{uuid}-vless#BPB-VLESS-WS-TLS-{hostname.split('.')[0]}"
    configs.append(vless_ws_tls)

    # Pattern 2: VLESS WS TLS on port 8443
    vless_ws_8443 = f"vless://{uuid}@{hostname}:8443?encryption=none&security=tls&sni={hostname}&type=ws&host={hostname}&path=%2F{uuid}-vless#BPB-VLESS-WS-8443-{hostname.split('.')[0]}"
    configs.append(vless_ws_8443)

    # Pattern 3: VLESS GRPC TLS
    vless_grpc = f"vless://{uuid}@{hostname}:443?encryption=none&security=tls&sni={hostname}&type=grpc&serviceName={uuid}-grpc&host={hostname}#BPB-VLESS-GRPC-TLS-{hostname.split('.')[0]}"
    configs.append(vless_grpc)

    # Pattern 4: Trojan WS TLS (if proxy_ip is provided, use it; otherwise worker domain)
    trojan_host = proxy_ip if proxy_ip.strip() else hostname
    trojan_ws = f"trojan@{trojan_host}:443?security=tls&sni={hostname}&type=ws&host={hostname}&path=%2Ftrojan%2F{uuid}#BPB-Trojan-WS-TLS-{hostname.split('.')[0]}"
    # Fix: proper trojan URL format
    trojan_ws = f"trojan://{uuid}@{trojan_host}:443?security=tls&sni={hostname}&type=ws&host={hostname}&path=%2Ftrojan%2F{uuid}#BPB-Trojan-WS-TLS-{hostname.split('.')[0]}"
    configs.append(trojan_ws)

    # Pattern 5: VLESS WS on alternative TLS ports
    for alt_port in [2053, 2083, 2087, 2096]:
        vless_alt = f"vless://{uuid}@{hostname}:{alt_port}?encryption=none&security=tls&sni={hostname}&type=ws&host={hostname}&path=%2F{uuid}-vless#BPB-VLESS-WS-{alt_port}-{hostname.split('.')[0]}"
        configs.append(vless_alt)

    return configs


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
        # Skip error messages from fetch_url_text
        if s.startswith("[HTTP Error") or s.startswith("[URL Error") or s.startswith("[Fetch Error"):
            continue
        # Skip HTML content (from error pages)
        if s.startswith("<!") or s.startswith("<html") or s.startswith("<!--") or s.startswith("</"):
            continue
        # Skip lines that are clearly HTML tags
        if s.startswith("<") and (">" in s) and not s.startswith("<vless") and not s.startswith("<trojan"):
            continue
        out.append(s)
    return out


def is_fetch_error(text: str) -> bool:
    """Check if the text is a fetch error message."""
    if not text:
        return False
    return text.startswith("[HTTP Error") or text.startswith("[URL Error") or text.startswith("[Fetch Error")


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
    # Handle URL-safe Base64: replace - with + and _ with /
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s.encode(), validate=False).decode("utf-8", errors="ignore")
    except Exception:
        # Fallback: try urlsafe_b64decode
        try:
            return base64.urlsafe_b64decode(s.encode()).decode("utf-8", errors="ignore")
        except Exception:
            return ""


def _b64url_encode(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode().rstrip("=")


def parse_share_link(raw: str) -> Optional[ParsedConfig]:
    """Parse a share link into a ParsedConfig. Returns None on any error."""
    try:
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
            try:
                port = int(p.port or (443 if security in {"tls", "reality"} else 80))
            except (ValueError, TypeError):
                port = 443
            path = _qget(q, "path", "/") or "/"
            sni = _qget(q, "sni", _qget(q, "peer", p.hostname)) or p.hostname
            ws_host = _qget(q, "host", sni) or sni
            display = p.fragment or f"{scheme.upper()} {p.hostname}:{port}"
            return ParsedConfig(raw, scheme, p.hostname, port, security, network, path, sni, ws_host, p.username or "", p.fragment, display)

        if scheme == "vmess":
            try:
                payload = _b64url_decode(raw.split("://", 1)[1])
                if not payload:
                    return None
                data = json.loads(payload)
                if not isinstance(data, dict):
                    return None
                host = str(data.get("add") or "").strip()
                if not host:
                    return None
                try:
                    port = int(data.get("port") or 443)
                except (ValueError, TypeError):
                    port = 443
                network = str(data.get("net") or data.get("type") or "tcp")
                security = "tls" if str(data.get("tls") or "").lower() == "tls" or port in TLS_PORTS else ""
                path = str(data.get("path") or "/")
                sni = str(data.get("sni") or data.get("host") or host)
                ws_host = str(data.get("host") or sni)
                ps = str(data.get("ps") or f"VMESS {host}:{port}")
                return ParsedConfig(raw, scheme, host, port, security, network, path, sni, ws_host, str(data.get("id") or ""), ps, ps)
            except (json.JSONDecodeError, ValueError, TypeError):
                return None

        # WireGuard/WARP configs are kept in subscription outputs but are not deeply modified/tested here.
        return None
    except Exception:
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
        try:
            port = int(p.port or default_port)
        except (ValueError, TypeError):
            port = default_port
        return p.hostname, port
    p = urlparse("//" + endpoint)
    if p.hostname:
        try:
            port = int(p.port or default_port)
        except (ValueError, TypeError):
            port = default_port
        return p.hostname, port
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
    try:
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
    except Exception:
        return raw_config.strip()


def _replace_vmess(raw_config: str, endpoint: str) -> str:
    try:
        payload = _b64url_decode(raw_config.split("://", 1)[1])
        if not payload:
            return raw_config.strip()
        data = json.loads(payload)
        if not isinstance(data, dict):
            return raw_config.strip()
        old_host = str(data.get("add") or "").strip()
        try:
            old_port = int(data.get("port") or 443)
        except (ValueError, TypeError):
            old_port = 443
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
    """Replace the endpoint in a config. Returns original config on ANY error."""
    try:
        scheme = urlparse(raw_config.strip()).scheme.lower()
        if scheme in {"vless", "trojan"}:
            return _replace_vless_trojan(raw_config, endpoint)
        if scheme == "vmess":
            return _replace_vmess(raw_config, endpoint)
        return raw_config.strip()
    except Exception:
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
    """Test a single config. Wrapped in try/except to never crash."""
    try:
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
    except Exception as e:
        return ScanResult(False, 0, 999999, "-", raw_config, f"Error: {str(e)[:120]}", "Error", "-")


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
    """Choose the best config using Nova-aware ranking when available."""
    try:
        from nova_core import choose_nova_best
        nova_best = choose_nova_best(results)
        if nova_best:
            return nova_best
    except Exception:
        pass
    working = [r for r in results if r.ok and r.score >= WORKING_CONFIG_MIN_SCORE]
    if not working:
        # Fallback: any ok result
        working = [r for r in results if r.ok]
    if not working:
        return results[0] if results else None
    # Sort by highest score, then lowest latency
    working.sort(key=lambda r: (-r.score, r.latency_ms))
    return working[0]


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

    # Best config with summary section
    if best:
        summary_lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║             BPB/Nova Easy Active Config v2 - Best           ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Score:    {best.score:<46} ║",
            f"║  Latency:  {best.latency_ms}ms{'':<42} ║",
            f"║  Endpoint: {best.endpoint:<46} ║",
            f"║  Scheme:   {best.scheme:<46} ║",
            f"║  Name:     {best.config_name:<46} ║",
            f"║  Message:  {best.message[:46]:<46} ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            best.config,
        ]
        files["best"].write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    else:
        files["best"].write_text("", encoding="utf-8")

    # Only include configs that scored >= WORKING_CONFIG_MIN_SCORE in working_configs.txt
    working = [r.config for r in results if r.ok and r.score >= WORKING_CONFIG_MIN_SCORE]
    if not working:
        # Fallback: include any ok config even if score is low
        working = [r.config for r in results if r.ok]
    files["working"].write_text("\n".join(working) + ("\n" if working else ""), encoding="utf-8")
    files["top"].write_text("\n".join([r.config for r in results[:50] if r.config]) + ("\n" if results else ""), encoding="utf-8")
    report_lines = [
        "گزارش BPB/Nova Easy Active Config v2",
        "=" * 42,
        f"کانفیگ‌های پایه: {len(base_configs)}",
        f"کانفیگ‌های تولیدشده/تست‌شده: {len(generated_configs)}",
        f"نتایج تست: {len(results)}",
        f"کانفیگ‌های سالم (score >= {WORKING_CONFIG_MIN_SCORE}): {len(working)}",
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

    # Nova Easy Mode outputs: config-only, bundle JSON, Clash/Mihomo YAML, and a Persian report.
    try:
        from nova_core import write_nova_outputs
        files.update({k: Path(v) for k, v in write_nova_outputs(root, base_configs, generated_configs, results, best).items()})
    except Exception as e:
        (out_dir / "nova_output_error.txt").write_text(str(e), encoding="utf-8")

    return {k: str(v) for k, v in files.items()}
