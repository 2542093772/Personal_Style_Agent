import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / "telegram_bot" / ".env", override=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from life.daily_planner import build_daily_plan
from life.daily_briefing import render_daily_briefing
from research.learning_report import render_learning_push_summary
from life.weather_open_meteo import get_today_weather
from shopping.ideal_wardrobe import build_purchase_advice
from shopping.shopping_briefing import render_purchase_advice

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
POLL_TIMEOUT = int(os.getenv("TELEGRAM_POLL_TIMEOUT", "25"))

if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN 未配置")

BASE = f"https://api.telegram.org/bot{TOKEN}"


def _json(path, default):
    p = ROOT / path
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _get_json(url):
    with urllib.request.urlopen(url, timeout=POLL_TIMEOUT + 10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_message(chat_id, text):
    body = urllib.parse.urlencode({
        "chat_id": str(chat_id),
        "text": text[:3900],
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/sendMessage", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_updates(offset=None):
    params = {"timeout": POLL_TIMEOUT, "allowed_updates": json.dumps(["message"])}
    if offset is not None:
        params["offset"] = offset
    return _get_json(f"{BASE}/getUpdates?{urllib.parse.urlencode(params)}")


def _weather_from_config():
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "config" / "daily_assistant.yaml").read_text(encoding="utf-8")) or {}
        location = ((cfg.get("weather") or {}).get("location") or "").strip()
        return get_today_weather(location) if location else None
    except Exception:
        return None


def command_today():
    weather = _weather_from_config()
    plan = build_daily_plan({"weather": weather})
    return render_daily_briefing(plan)


def command_report():
    report = _json("reports/daily_learning_survey.json", {})
    if not report:
        return "今天还没有学习调查报告。可以先运行：python scheduler/jobs.py daily"
    return render_learning_push_summary(report)


def command_wardrobe():
    wardrobe = _json("data/wardrobe.json", [])
    if not wardrobe:
        return "衣柜目前还是空的。把衣服录入 data/wardrobe.json 后，我就能从现有衣服里给你搭配。"

    lines = [f"衣柜共 {len(wardrobe)} 件："]
    for item in wardrobe[:50]:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("title") or "未命名单品"
        category = item.get("category") or "未分类"
        color = item.get("color") or ""
        lines.append(f"- [{category}] {name}" + (f"｜{color}" if color else ""))
    return "\n".join(lines)


def command_shop():
    advice = build_purchase_advice(include_live_links=True, limit=3)
    return render_purchase_advice(advice)


def command_help():
    return (
        "可用命令：\n"
        "/today - 今天的穿搭与生活方案\n"
        "/report - 今日学习调查摘要\n"
        "/wardrobe - 当前衣柜状态\n"
        "/shop - 当前最值得补的单品与购买链接\n"
        "/help - 查看命令"
    )


def handle_message(message):
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    if not chat_id:
        return

    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
        return

    text = (message.get("text") or "").strip()
    command = text.split()[0].split("@")[0].lower() if text else ""

    if command in {"/start", "/help"}:
        reply = "Personal Style Agent 已连接。\n\n" + command_help()
    elif command == "/today":
        reply = command_today()
    elif command == "/report":
        reply = command_report()
    elif command == "/wardrobe":
        reply = command_wardrobe()
    elif command == "/shop":
        reply = command_shop()
    else:
        reply = "我目前先支持固定命令。\n\n" + command_help()

    send_message(chat_id, reply)


def main():
    print("Telegram bot starting...", flush=True)
    try:
        me = _get_json(f"{BASE}/getMe")
        username = (me.get("result") or {}).get("username", "")
        print(f"Telegram API connected. Bot: @{username}" if username else "Telegram API connected.", flush=True)
    except Exception as exc:
        print("Telegram API connection failed:", repr(exc), flush=True)
        print("Run: python -u telegram_bot/diagnose.py", flush=True)
        return

    print("Telegram bot polling started. Ctrl+C to stop.", flush=True)
    offset = None
    while True:
        try:
            data = get_updates(offset)
            for update in data.get("result", []):
                offset = int(update["update_id"]) + 1
                message = update.get("message")
                if message:
                    handle_message(message)
        except KeyboardInterrupt:
            print("Stopped.", flush=True)
            break
        except Exception as exc:
            print("Polling error:", repr(exc), flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
