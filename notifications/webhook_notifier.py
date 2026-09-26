import json
import os
import urllib.request
from typing import Dict, Any


def push_daily_briefing(message: str, payload: Dict[str, Any] | None = None):
    url = os.getenv("LIFE_ASSISTANT_WEBHOOK_URL", "").strip()
    if not url:
        return {
            "ok": False,
            "sent": False,
            "reason": "LIFE_ASSISTANT_WEBHOOK_URL is not configured",
        }

    body = {
        "text": message,
        "type": "daily_life_briefing",
        "data": payload or {},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {
                "ok": 200 <= resp.status < 300,
                "sent": True,
                "status": resp.status,
            }
    except Exception as exc:
        return {
            "ok": False,
            "sent": False,
            "reason": str(exc),
        }
