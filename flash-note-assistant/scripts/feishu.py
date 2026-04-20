#!/usr/bin/env python3
"""Feishu OpenAPI client — shared by all flash-note scripts."""

import json
from typing import Any
from pathlib import Path
from urllib import error, request

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict[str, Any]:
    data = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def resolve_api_base(domain: str | None) -> str:
    normalized = (domain or "feishu").strip().rstrip("/")
    if normalized in ("", "feishu"):
        return "https://open.feishu.cn/open-apis"
    if normalized == "lark":
        return "https://open.larksuite.com/open-apis"
    if normalized.endswith("/open-apis"):
        return normalized
    return f"{normalized}/open-apis"


def feishu_request(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    req_headers = dict(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json; charset=utf-8"

    req = request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"feishu api http error {exc.code}: {raw}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"feishu api request failed: {exc.reason}") from exc

    result = json.loads(raw)
    if not isinstance(result, dict):
        raise RuntimeError("feishu api returned non-object payload")
    return result


def fetch_tenant_access_token(api_base: str, *, app_id: str, app_secret: str) -> str:
    resp = feishu_request(
        method="POST",
        url=f"{api_base}/auth/v3/tenant_access_token/internal",
        headers={},
        payload={"app_id": app_id, "app_secret": app_secret},
    )
    token = str(resp.get("tenant_access_token", "")).strip()
    if resp.get("code") != 0 or not token:
        raise RuntimeError(f'failed to get tenant access token: {resp.get("msg") or resp}')
    return token
