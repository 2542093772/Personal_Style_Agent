import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "telegram_bot" / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not TOKEN:
    raise SystemExit("请先设置环境变量 TELEGRAM_BOT_TOKEN")

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
with urllib.request.urlopen(url, timeout=20) as resp:
    data = json.loads(resp.read().decode("utf-8"))

results = data.get("result", [])
if not results:
    raise SystemExit("暂时没有消息。请先在 Telegram 里打开你的 Bot，点 Start 并发送一条消息，然后重新运行。")

seen = set()
for update in results:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None or chat_id in seen:
        continue
    seen.add(chat_id)
    print("chat_id:", chat_id)
    print("type:", chat.get("type"))
    print("name:", chat.get("first_name") or chat.get("title") or "")
    print("---")
