# -*- coding: utf-8 -*-
"""Cloudflare deploy helper for the internal BPB Wizard flow.

This module never opens GitHub. It deploys the local Worker bundle to the user's own
Cloudflare account when the user provides a valid Cloudflare API token and Account ID.
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CF_API = "https://api.cloudflare.com/client/v4"
ACCOUNT_ID_RE = re.compile(r"^[0-9a-f]{32}$", re.I)


def explain_cloudflare_error(message: str) -> str:
    msg = str(message or "")
    if "/accounts/cfat_" in msg or "/accounts/cfut_" in msg or "object identifier is invalid" in msg:
        return (
            "Account ID اشتباه وارد شده. مقدارهایی که با cfat_ یا cfut_ شروع می‌شوند API Token هستند، نه Account ID. "
            "داخل نرم‌افزار اول دکمه «تست Token و پیدا کردن Account ID» را بزن؛ یا در Cloudflare برو: "
            "Workers & Pages → Account details → Account ID → Click to copy. سپس همان شناسه ۳۲ کاراکتری را در فیلد Account ID بگذار."
        )
    if "workers.dev subdomain" in msg or "10063" in msg:
        return (
            "برای اکانت هنوز workers.dev ساخته نشده. در Cloudflare برو Workers & Pages را یک بار باز کن؛ "
            "اگر ازت subdomain خواست، یک نام ساده انتخاب کن. بعد دوباره Deploy را بزن."
        )
    if "Content-Type must be one of" in msg or "multipart/form-data" in msg or "application/javascript" in msg:
        return (
            "روش آپلود Worker باید multipart/form-data باشد، چون فایل داخلی BPB از Module Worker استفاده می‌کند. "
            "این نسخه Deploy Assistant همین مورد را خودکار اصلاح کرده است. اگر هنوز این خطا را دیدی، نسخه قدیمی برنامه را اجرا کرده‌ای؛ نسخه v9 را اجرا کن."
        )
    if "main_module" in msg or "body_part" in msg or "module" in msg:
        return (
            "Cloudflare فایل اصلی Worker را پیدا نکرده است. این نسخه metadata را با main_module=worker.js می‌فرستد. "
            "اگر خطا ادامه داشت، نام فایل worker.js را در پوشه integrated_sources تغییر نداده باش."
        )
    if "Authentication error" in msg or "Unable to authenticate" in msg or "10000" in msg:
        return (
            "Token دسترسی کافی ندارد یا اشتباه کپی شده. Token باید Permissionِ Workers Scripts: Edit داشته باشد "
            "و روی همین Account فعال باشد."
        )
    return msg


def validate_account_id(account_id: str) -> str:
    value = (account_id or "").strip()
    if not value:
        raise ValueError("Account ID خالی است. اول دکمه «تست Token و پیدا کردن Account ID» را بزن یا آن را از Cloudflare کپی کن.")
    lowered = value.lower()
    if lowered.startswith(("cfat_", "cfut_", "bearer ")):
        raise ValueError(
            "این مقدار Account ID نیست؛ این API Token است. Account ID معمولاً یک رشته ۳۲ کاراکتری از عدد و حروف a-f است. "
            "مسیر دقیق: Cloudflare Dashboard → Workers & Pages → Account details → Account ID → Click to copy."
        )
    if not ACCOUNT_ID_RE.match(value):
        raise ValueError(
            "فرمت Account ID درست نیست. Account ID باید شبیه یک رشته ۳۲ کاراکتری hexadecimal باشد، نه ایمیل، نه نام اکانت، نه Token. "
            "بهترین روش: Token را وارد کن و روی «تست Token و پیدا کردن Account ID» بزن تا نرم‌افزار خودش پر کند."
        )
    return value


def validate_worker_name(worker_name: str) -> str:
    name = (worker_name or "bpb-panel").strip().lower()
    name = re.sub(r"[^a-z0-9-]", "-", name).strip("-") or "bpb-panel"
    if len(name) > 63:
        name = name[:63].strip("-") or "bpb-panel"
    return name


def _request(method: str, url: str, token: str, data: dict | str | bytes | None = None, content_type: str = "application/json", timeout: int = 30) -> dict:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        token = token.split(None, 1)[1].strip()
    if not token:
        raise ValueError("Cloudflare API Token خالی است.")
    body = None
    if data is not None:
        if isinstance(data, bytes):
            body = data
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method=method.upper())
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", content_type)
    req.add_header("Accept", "application/json")
    try:
        with urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="ignore")
    except HTTPError as e:
        txt = e.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(txt)
        except Exception:
            payload = {"success": False, "errors": [{"message": txt or str(e)}]}
        payload.setdefault("success", False)
        for err in payload.get("errors", []) or []:
            if isinstance(err, dict):
                err["help_fa"] = explain_cloudflare_error(err.get("message", ""))
        return payload
    except URLError as e:
        return {"success": False, "errors": [{"message": str(e), "help_fa": "اتصال اینترنت یا دسترسی به api.cloudflare.com برقرار نیست."}]}
    try:
        payload = json.loads(txt)
    except Exception:
        payload = {"success": True, "raw": txt}
    if not payload.get("success", True):
        for err in payload.get("errors", []) or []:
            if isinstance(err, dict):
                err["help_fa"] = explain_cloudflare_error(err.get("message", ""))
    return payload


def verify_token(api_token: str) -> dict:
    return _request("GET", f"{CF_API}/user/tokens/verify", api_token)


def list_accounts(api_token: str) -> dict:
    return _request("GET", f"{CF_API}/accounts", api_token)


def get_workers_subdomain(api_token: str, account_id: str) -> dict:
    account_id = validate_account_id(account_id)
    return _request("GET", f"{CF_API}/accounts/{account_id}/workers/subdomain", api_token)



def _multipart_bytes(parts: list[dict]) -> tuple[bytes, str]:
    """Build a small multipart/form-data body without external dependencies.

    Each part dict accepts: name, value bytes/str, filename optional, content_type optional.
    Cloudflare's Worker module upload expects a metadata part and one or more file parts.
    """
    boundary = "----BPBEasyCloudflareBoundary" + secrets.token_hex(16)
    chunks: list[bytes] = []
    for part in parts:
        name = part["name"]
        filename = part.get("filename")
        content_type = part.get("content_type") or "application/octet-stream"
        value = part.get("value", b"")
        if isinstance(value, str):
            value = value.encode("utf-8")
        disposition = f'form-data; name="{name}"'
        if filename:
            disposition += f'; filename="{filename}"'
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f"Content-Disposition: {disposition}\r\n".encode("utf-8"))
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(value)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _request_raw(method: str, url: str, token: str, body: bytes, content_type: str, timeout: int = 45) -> dict:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        token = token.split(None, 1)[1].strip()
    if not token:
        raise ValueError("Cloudflare API Token خالی است.")
    req = Request(url, data=body, method=method.upper())
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", content_type)
    req.add_header("Accept", "application/json")
    req.add_header("Content-Length", str(len(body)))
    try:
        with urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="ignore")
    except HTTPError as e:
        txt = e.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(txt)
        except Exception:
            payload = {"success": False, "errors": [{"message": txt or str(e)}]}
        payload.setdefault("success", False)
        for err in payload.get("errors", []) or []:
            if isinstance(err, dict):
                err["help_fa"] = explain_cloudflare_error(err.get("message", ""))
        return payload
    except URLError as e:
        return {"success": False, "errors": [{"message": str(e), "help_fa": "اتصال اینترنت یا دسترسی به api.cloudflare.com برقرار نیست."}]}
    try:
        payload = json.loads(txt)
    except Exception:
        payload = {"success": True, "raw": txt}
    if not payload.get("success", True):
        for err in payload.get("errors", []) or []:
            if isinstance(err, dict):
                err["help_fa"] = explain_cloudflare_error(err.get("message", ""))
    return payload


def _upload_module_worker(api_token: str, account_id: str, worker_name: str, script: str) -> dict:
    metadata = {
        "main_module": "worker.js",
        "compatibility_date": date.today().isoformat(),
        "compatibility_flags": ["nodejs_compat"],
        "annotations": {
            "workers/message": "Deploy from BPB Easy Active Config v9",
            "workers/tag": "bpb-easy-v9"
        }
    }
    body, ctype = _multipart_bytes([
        {
            "name": "metadata",
            "value": json.dumps(metadata, ensure_ascii=False),
            "content_type": "application/json",
        },
        {
            "name": "worker.js",
            "filename": "worker.js",
            "value": script,
            "content_type": "application/javascript+module",
        },
    ])
    url = f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}"
    return _request_raw("PUT", url, api_token, body, ctype)

def deploy_worker_script(api_token: str, account_id: str, worker_name: str, script_path: str | Path, uuid: str = "", sub_path: str = "sub", proxy_ip: str = "") -> dict:
    account_id = validate_account_id(account_id)
    worker_name = validate_worker_name(worker_name)
    script_path = Path(script_path)
    if not script_path.exists():
        return {"success": False, "errors": [{"message": f"worker.js پیدا نشد: {script_path}"}]}
    script = script_path.read_text(encoding="utf-8", errors="ignore")
    script = script.replace("__BPB_UUID__", (uuid or "").strip())
    script = script.replace("__BPB_SUB_PATH__", (sub_path or "sub").strip().strip("/") or "sub")
    script = script.replace("__BPB_PROXY_IP__", (proxy_ip or "").strip())
    if "addEventListener" not in script and "export default" not in script:
        return {"success": False, "errors": [{"message": "فایل worker.js شبیه Worker معتبر نیست."}]}
    return _upload_module_worker(api_token, account_id, worker_name, script)


def enable_worker_subdomain_route(api_token: str, account_id: str, worker_name: str) -> dict:
    account_id = validate_account_id(account_id)
    worker_name = validate_worker_name(worker_name)
    url = f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}/subdomain"
    return _request("POST", url, api_token, {"enabled": True}, content_type="application/json")
