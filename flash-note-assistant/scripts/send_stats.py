#!/usr/bin/env python3
"""Fetch task stats and send to Weixin via iLink."""

import base64
import json
import os
import secrets
import subprocess
import sys
import urllib.request
import urllib.error
import uuid
from pathlib import Path


def _random_wechat_uin():
    return base64.b64encode(str(secrets.randbelow(2**32)).encode()).decode()


def _send_message(base_url, token, to_user_id, text, client_id, context_token=""):
    message = {
        "from_user_id": "",
        "to_user_id": to_user_id,
        "client_id": client_id,
        "message_type": 2,
        "message_state": 2,
        "item_list": [{"type": 1, "text_item": {"text": text}}],
    }
    if context_token:
        message["context_token"] = context_token

    body = json.dumps({
        "msg": message,
        "base_info": {"channel_version": "2.2.0"},
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "Content-Length": str(len(body)),
        "X-WECHAT-UIN": _random_wechat_uin(),
        "iLink-App-Id": "bot",
        "iLink-App-ClientVersion": "66048",
        "Authorization": f"Bearer {token}",
    }

    url = f"{base_url.rstrip('/')}/ilink/bot/sendmessage"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    weixin_token = os.getenv("WEIXIN_TOKEN", "")
    weixin_account_id = os.getenv("WEIXIN_ACCOUNT_ID", "")
    weixin_base_url = os.getenv("WEIXIN_BASE_URL", "https://ilinkai.weixin.qq.com")
    weixin_home_channel = os.getenv("WEIXIN_HOME_CHANNEL", "")

    if not weixin_token or not weixin_account_id or not weixin_home_channel:
        missing = []
        if not weixin_token:
            missing.append("WEIXIN_TOKEN")
        if not weixin_account_id:
            missing.append("WEIXIN_ACCOUNT_ID")
        if not weixin_home_channel:
            missing.append("WEIXIN_HOME_CHANNEL")
        print(f"ERROR: Missing Weixin env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Load context token
    context_token = ""
    tokens_dir = os.path.join(os.environ.get("HERMES_HOME", "/root/.hermes"), "weixin", "accounts")
    ct_path = Path(tokens_dir, f"{weixin_account_id}.context-tokens.json")
    if ct_path.exists():
        try:
            tokens = json.loads(ct_path.read_text(encoding="utf-8"))
            context_token = tokens.get(weixin_home_channel, "")
        except Exception:
            pass

    # Get stats — call sibling stats.py
    stats_script = str(Path(__file__).resolve().parent / "stats.py")
    try:
        result = subprocess.run(
            ["python3", stats_script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            stats_text = f"⚠️ 统计失败：{result.stderr.strip()}"
        else:
            stats_text = result.stdout
    except subprocess.TimeoutExpired:
        stats_text = "⚠️ 统计超时：脚本执行超过 30 秒"
    except Exception as e:
        stats_text = f"⚠️ 统计异常：{e}"

    # Send
    try:
        resp = _send_message(
            weixin_base_url, weixin_token, weixin_home_channel,
            stats_text, f"hermes-weixin-{uuid.uuid4().hex}", context_token
        )
        errcode = resp.get("errcode", 0)
        if errcode == 0:
            print(f"Sent OK: {json.dumps(resp, ensure_ascii=False)}")
        else:
            print(f"Sent but API returned errcode={errcode}: {resp.get('errmsg', '')}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Send failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
