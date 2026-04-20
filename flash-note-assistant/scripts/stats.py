#!/usr/bin/env python3
"""Query Feishu Bitable, render grouped task stats."""

import json
import sys
from typing import Any
from urllib import parse

from feishu import fetch_tenant_access_token, feishu_request, load_config, resolve_api_base

STATUS_FIELD = "处理状态"
TITLE_FIELD = "摘要"


def normalize_field_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts).strip()
    if isinstance(value, dict):
        return str(value.get("text", "")).strip()
    return str(value).strip()


def group_records(
    records: list[dict[str, Any]], *, status_field: str = STATUS_FIELD, title_field: str = TITLE_FIELD
) -> dict[str, list[str]]:
    groups = {"待处理": [], "稍后": [], "已完成": [], "已归档": [], "未知状态": []}
    for record in records:
        fields = record.get("fields", {})
        if not isinstance(fields, dict):
            fields = {}
        status = normalize_field_text(fields.get(status_field, ""))
        title = normalize_field_text(fields.get(title_field, ""))
        if not title:
            title = str(record.get("record_id") or record.get("id") or "未命名记录").strip()
        groups[status if status in groups else "未知状态"].append(title)
    return groups


def render_markdown(groups: dict[str, list[str]], *, total_records: int) -> str:
    pending = groups["待处理"]
    later = groups["稍后"]
    done = groups["已完成"]
    archived = groups["已归档"]
    unknown = groups["未知状态"]

    lines = [
        "**📊 任务统计报告**",
        "————————————",
        f"**待处理任务：{len(pending)} 项**",
    ]
    for title in pending:
        lines.append(f"· {title}")
    lines.append(f"**稍后处理：{len(later)} 项**")
    for title in later:
        lines.append(f"· {title}")
    lines.append(f"**已完成：{len(done)} 项**")
    lines.append(f"**已归档：{len(archived)} 项**")
    if unknown:
        lines.append(f"**未知状态：{len(unknown)} 项**")
    lines.append(f"**总计：{total_records} 条记录**")
    return "\n".join(lines)


def render_error_markdown(exc: Exception) -> str:
    reason = str(exc).strip() or exc.__class__.__name__
    return "\n".join([
        "**⚠️ 任务统计失败**",
        f"**原因：{reason}**",
        "**处理建议：请稍后重试；若持续失败，请检查飞书权限、网络或统计配置。**",
    ])


def fetch_all_records(config: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    app_id = str(config.get("appId", "")).strip()
    app_secret = str(config.get("appSecret", "")).strip()
    if not app_id or not app_secret:
        raise RuntimeError("config.json missing appId or appSecret")

    app_token = str(config.get("app_token", "")).strip()
    table_id = str(config.get("table_id", "")).strip()
    if not app_token or not table_id:
        raise RuntimeError("config.json missing app_token or table_id")

    domain = str(config.get("domain", "feishu")).strip() or "feishu"
    api_base = resolve_api_base(domain)
    access_token = fetch_tenant_access_token(api_base, app_id=app_id, app_secret=app_secret)

    headers = {"Authorization": f"Bearer {access_token}"}
    items: list[dict[str, Any]] = []
    page_token: str | None = None
    total: int | None = None

    while True:
        query = {"page_size": int(config.get("page_size", 500))}
        if page_token:
            query["page_token"] = page_token
        url = (
            f"{api_base}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?"
            f"{parse.urlencode(query)}"
        )
        resp = feishu_request(
            method="POST",
            url=url,
            headers=headers,
            payload={"field_names": [TITLE_FIELD, STATUS_FIELD], "automatic_fields": False},
        )

        if resp.get("code") != 0:
            raise RuntimeError(f'failed to search bitable records: {resp.get("msg") or resp}')

        data = resp.get("data")
        if not isinstance(data, dict):
            raise RuntimeError("bitable search response missing data")

        batch = data.get("items")
        if not isinstance(batch, list):
            raise RuntimeError("bitable search response missing items list")

        items.extend(r for r in batch if isinstance(r, dict))

        raw_total = data.get("total")
        if isinstance(raw_total, int):
            total = raw_total

        if not data.get("has_more"):
            break
        next_token = data.get("page_token")
        page_token = str(next_token).strip() if next_token else None

    return items, total if total is not None else len(items)


def main() -> int:
    try:
        config = load_config()
        records, total_records = fetch_all_records(config)
        groups = group_records(records)
        print(render_markdown(groups, total_records=total_records))
        return 0
    except Exception as exc:
        print(render_error_markdown(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
