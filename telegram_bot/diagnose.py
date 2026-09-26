import json
import os
import socket
import urllib.parse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / "telegram_bot" / ".env", override=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

print("=== Telegram Bot Diagnostic ===", flush=True)
print("TOKEN configured:", bool(TOKEN), flush=True)
print("CHAT_ID configured:", bool(CHAT_ID), flush=True)

if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN 未配置")

host = "api.telegram.org"

try:
    ip = socket.gethostbyname(host)
    print("DNS:", host, "->", ip, flush=True)
except Exception as exc:
    print("DNS FAILED:", repr(exc), flush=True)
    raise SystemExit(2)

base = f"https://api.telegram.org/bot{TOKEN}"

def get_json(url, timeout=12):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

try:
    status, me = get_json(base + "/getMe")
    print("getMe HTTP:", status, flush=True)
    print("getMe ok:", me.get("ok"), flush=True)
    if me.get("result"):
        print("bot username:", me["result"].get("username"), flush=True)
except Exception as exc:
    print("getMe FAILED:", repr(exc), flush=True)
    print("Python 当前无法正常访问 Telegram Bot API。", flush=True)
    raise SystemExit(3)

try:
    status, updates = get_json(base + "/getUpdates?timeout=1")
    print("getUpdates HTTP:", status, flush=True)
    print("update count:", len(updates.get("result", [])), flush=True)
    for update in updates.get("result", [])[-3:]:
        msg = update.get("message") or {}
        chat = msg.get("chat") or {}
        print(
            "update:",
            update.get("update_id"),
            "chat_id=", chat.get("id"),
            "text=", repr(msg.get("text")),
            flush=True,
        )
except Exception as exc:
    print("getUpdates FAILED:", repr(exc), flush=True)

if CHAT_ID:
    try:
        body = urllib.parse.urlencode({
            "chat_id": CHAT_ID,
            "text": "✅ Personal Style Agent Telegram 连接测试成功",
        }).encode("utf-8")
        req = urllib.request.Request(base + "/sendMessage", data=body, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        print("sendMessage ok:", payload.get("ok"), flush=True)
    except Exception as exc:
        print("sendMessage FAILED:", repr(exc), flush=True)
else:
    print("未配置 TELEGRAM_CHAT_ID，跳过主动发消息测试。", flush=True)

print("=== Diagnostic Complete ===", flush=True)
