import json
import os
import urllib.parse
import urllib.request

from flask import Flask, Response, jsonify, request

from reports.daily_report import render_daily_html
from life.daily_planner import build_daily_plan

from telegram_bot.bot import (
    ALLOWED_CHAT_ID,
    BASE,
    command_help,
    command_report,
    command_shop,
    command_today,
    command_wardrobe,
    send_message,
)

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()


def _reply_for(text: str) -> str:
    text = (text or "").strip()
    command = text.split()[0].split("@")[0].lower() if text else ""

    if command in {"/start", "/help"}:
        return "Personal Style Agent 云端已连接。\n\n" + command_help()
    if command == "/today":
        return command_today()
    if command == "/report":
        return command_report()
    if command == "/wardrobe":
        return command_wardrobe()
    if command == "/shop":
        return command_shop()
    return "我目前先支持固定命令。\n\n" + command_help()


def register_commands():
    commands = [
        {"command": "today", "description": "查看今天的穿搭与生活方案"},
        {"command": "report", "description": "查看今日学习调查摘要"},
        {"command": "wardrobe", "description": "查看当前衣柜状态"},
        {"command": "shop", "description": "查看最值得补的单品与购买链接"},
        {"command": "help", "description": "查看可用命令"},
    ]
    req = urllib.request.Request(
        f"{BASE}/setMyCommands",
        data=json.dumps({"commands": commands}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register_webhook():
    external_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if not external_url:
        return {"ok": False, "reason": "RENDER_EXTERNAL_URL unavailable"}

    webhook_url = external_url.rstrip("/") + "/telegram/webhook"
    body = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": False,
    }
    if WEBHOOK_SECRET:
        body["secret_token"] = WEBHOOK_SECRET

    req = urllib.request.Request(
        f"{BASE}/setWebhook",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


@app.get("/")
def index():
    return jsonify({
        "service": "Personal Style Agent Telegram Cloud Bot",
        "status": "ok",
    })


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/report/today")
def report_today():
    survey_path = os.path.join("reports", "daily_learning_survey.json")
    survey = {}
    try:
        if os.path.exists(survey_path):
            with open(survey_path, "r", encoding="utf-8") as fh:
                survey = json.load(fh)
    except Exception:
        survey = {}

    plan = build_daily_plan({})
    return Response(render_daily_html(plan, survey), mimetype="text/html")


@app.post("/telegram/webhook")
def telegram_webhook():
    if WEBHOOK_SECRET:
        supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if supplied != WEBHOOK_SECRET:
            return jsonify({"ok": False, "error": "forbidden"}), 403

    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))

    if not chat_id:
        return jsonify({"ok": True, "ignored": "no_chat"})

    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
        return jsonify({"ok": True, "ignored": "unauthorized_chat"})

    reply = _reply_for(message.get("text", ""))
    send_message(chat_id, reply)
    return jsonify({"ok": True})


@app.post("/admin/register-webhook")
def admin_register_webhook():
    supplied = request.headers.get("X-Admin-Secret", "")
    admin_secret = os.getenv("CLOUD_ADMIN_SECRET", "").strip()
    if not admin_secret or supplied != admin_secret:
        return jsonify({"ok": False, "error": "forbidden"}), 403

    try:
        return jsonify(register_webhook())
    except Exception as exc:
        return jsonify({"ok": False, "error": repr(exc)}), 500


if os.getenv("RENDER", "").lower() == "true":
    try:
        result = register_webhook()
        print("Telegram webhook registration:", result, flush=True)
        commands_result = register_commands()
        print("Telegram command registration:", commands_result, flush=True)
    except Exception as exc:
        print("Telegram webhook registration failed:", repr(exc), flush=True)
