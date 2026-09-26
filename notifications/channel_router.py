import json
import os
import urllib.parse
import urllib.request


def _post_json(url, body, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return {"ok": 200 <= resp.status < 300, "sent": True, "status": resp.status}


def _generic(message):
    url = os.getenv("LIFE_ASSISTANT_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "sent": False, "reason": "LIFE_ASSISTANT_WEBHOOK_URL 未配置"}
    return _post_json(url, {"text": message, "type": "daily_life_briefing"})


def _feishu(message):
    url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "sent": False, "reason": "FEISHU_WEBHOOK_URL 未配置"}
    return _post_json(url, {"msg_type": "text", "content": {"text": message}})


def _wecom(message):
    url = os.getenv("WECOM_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "sent": False, "reason": "WECOM_WEBHOOK_URL 未配置"}
    return _post_json(url, {"msgtype": "text", "text": {"content": message}})


def _telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return {"ok": False, "sent": False, "reason": "Telegram 配置不完整"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return {"ok": 200 <= resp.status < 300, "sent": True, "status": resp.status}


def push_message(message: str, channel: str = "auto"):
    channel = (channel or "auto").lower()

    if channel == "auto":
        if os.getenv("FEISHU_WEBHOOK_URL"):
            channel = "feishu"
        elif os.getenv("WECOM_WEBHOOK_URL"):
            channel = "wecom"
        elif os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            channel = "telegram"
        else:
            channel = "webhook"

    handlers = {
        "feishu": _feishu,
        "wecom": _wecom,
        "telegram": _telegram,
        "webhook": _generic,
    }
    handler = handlers.get(channel)
    if not handler:
        return {"ok": False, "sent": False, "reason": f"不支持的推送渠道: {channel}"}

    try:
        result = handler(message)
        result["channel"] = channel
        return result
    except Exception as exc:
        return {"ok": False, "sent": False, "channel": channel, "reason": str(exc)}
