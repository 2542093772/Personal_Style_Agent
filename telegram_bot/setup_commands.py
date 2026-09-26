import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / "telegram_bot" / ".env", override=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN 未配置")

commands = [
    {"command": "today", "description": "查看今天的穿搭与生活方案"},
    {"command": "report", "description": "查看今日学习调查摘要"},
    {"command": "wardrobe", "description": "查看当前衣柜状态"},
    {"command": "help", "description": "查看可用命令"},
]

url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
body = json.dumps({"commands": commands}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    url,
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=20) as resp:
    result = json.loads(resp.read().decode("utf-8"))

print(json.dumps(result, ensure_ascii=False, indent=2))
