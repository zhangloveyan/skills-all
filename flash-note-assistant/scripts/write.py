#!/usr/bin/env python3
"""Create one Feishu Bitable record from stdin JSON."""

import json
import sys
from typing import Any

from feishu import fetch_tenant_access_token, feishu_request, load_config, resolve_api_base

SUMMARY_FIELD = "摘要"
CATEGORY_FIELD = "分类"
STATUS_FIELD = "处理状态"
RAW_INFO_FIELD = "原始信息"

ALLOWED_CATEGORIES = {"待办任务", "灵感随想", "信息存档"}
ALLOWED_STATUSES = {"待处理", "已完成", "稍后", "已归档"}


def normalize_text(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"{field_name} is required")
    return text


def validate_fields(payload: dict[str, Any]) -> dict[str, str]:
    summary = normalize_text(payload.get(SUMMARY_FIELD), field_name=SUMMARY_FIELD)
    if len(summary) > 15:
        raise RuntimeError(f"{SUMMARY_FIELD} must be 15 characters or fewer")

    category = normalize_text(payload.get(CATEGORY_FIELD), field_name=CATEGORY_FIELD)
    if category not in ALLOWED_CATEGORIES:
        raise RuntimeError(f"{CATEGORY_FIELD} must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}")

    status = normalize_text(payload.get(STATUS_FIELD, "待处理"), field_name=STATUS_FIELD)
    if status not in ALLOWED_STATUSES:
        raise RuntimeError(f"{STATUS_FIELD} must be one of: 待处理, 已完成, 稍后, 已归档")

    raw_info = normalize_text(payload.get(RAW_INFO_FIELD), field_name=RAW_INFO_FIELD)

    return {
        SUMMARY_FIELD: summary,
        CATEGORY_FIELD: category,
        STATUS_FIELD: status,
        RAW_INFO_FIELD: raw_info,
    }


def create_record(*, config: dict[str, Any], fields: dict[str, str]) -> dict[str, Any]:
    app_token = str(config.get("app_token", "")).strip()
    table_id = str(config.get("table_id", "")).strip()
    if not app_token or not table_id:
        raise RuntimeError("config.json missing app_token or table_id")

    app_id = str(config.get("appId", "")).strip()
    app_secret = str(config.get("appSecret", "")).strip()
    if not app_id or not app_secret:
        raise RuntimeError("config.json missing appId or appSecret")

    domain = str(config.get("domain", "feishu")).strip() or "feishu"
    api_base = resolve_api_base(domain)

    access_token = fetch_tenant_access_token(api_base, app_id=app_id, app_secret=app_secret)

    resp = feishu_request(
        method="POST",
        url=f"{api_base}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {access_token}"},
        payload={"fields": fields},
    )
    if resp.get("code") != 0:
        raise RuntimeError(f'failed to create bitable record: {resp.get("msg") or resp}')

    data = resp.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("bitable create response missing data")

    record = data.get("record")
    if not isinstance(record, dict):
        raise RuntimeError("bitable create response missing record")

    record_id = str(record.get("record_id", "")).strip()
    if not record_id:
        raise RuntimeError("bitable create response missing record_id")

    return {"ok": True, "record_id": record_id, "fields": fields}


def main() -> int:
    try:
        if sys.stdin.isatty():
            raise RuntimeError("missing stdin json payload")

        raw = sys.stdin.read()
        if not raw.strip():
            raise RuntimeError("missing stdin json payload")

        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise RuntimeError("stdin payload must be a json object")

        fields = validate_fields(payload)
        result = create_record(config=load_config(), fields=fields)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(
            json.dumps({"ok": False, "error": str(exc).strip() or exc.__class__.__name__}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
