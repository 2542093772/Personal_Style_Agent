import json
import os
import urllib.parse
import urllib.request
import threading

from flask import Flask, Response, jsonify, request

from reports.daily_report import render_daily_html
from life.daily_planner import build_daily_plan

from telegram_bot.bot import (
    ALLOWED_CHAT_ID,
    BASE,
    command_help,
    command_location,
    command_report,
    command_shop,
    command_today,
    command_wardrobe,
    send_message,
)
from life.location_state import detect_location_update, update_default_location
from runtime.manual_trigger import manual_refresh_needed, deliver_refresh_result

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
    if command == "/location":
        resolved = detect_location_update(text)
        if resolved:
            result = update_default_location(resolved, source_text=text)
            state = result["state"]
            persisted = result["persistence"].get("ok")
            suffix = "，并已同步为后续日报默认地点。" if persisted else "。当前云实例已更新；要跨部署长期保存还需配置 GitHub 位置同步令牌。"
            return f"默认地点已更新为：{state.get('display_name')}{suffix}"
        return command_location()

    resolved = detect_location_update(text)
    if resolved:
        result = update_default_location(resolved, source_text=text)
        state = result["state"]
        persisted = result["persistence"].get("ok")
        suffix = "，并已同步为后续日报默认地点。" if persisted else "。当前云实例已更新；要跨部署长期保存还需配置 GitHub 位置同步令牌。"
        return f"识别到你的位置变化，默认地点已更新为：{state.get('display_name')}{suffix}"

    return "我目前先支持固定命令。\n\n" + command_help()


def register_commands():
    commands = [
        {"command": "today", "description": "查看今天的穿搭与生活方案"},
        {"command": "report", "description": "查看今日学习调查摘要"},
        {"command": "wardrobe", "description": "查看当前衣柜状态"},
        {"command": "shop", "description": "查看最值得补的单品与购买链接"},
        {"command": "location", "description": "查看或更新默认地点"},
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
    report_path = os.path.join("reports", "daily_style_report.html")
    if not os.path.exists(report_path):
        return Response(
            "<h2>今日日报尚未生成</h2><p>系统会在每天 07:45 自动生成并推送。</p>",
            status=404,
            mimetype="text/html",
        )
    with open(report_path, "r", encoding="utf-8") as fh:
        return Response(fh.read(), mimetype="text/html")


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

    text = message.get("text", "")
    command = text.split()[0].split("@")[0].lower() if text else ""

    # Location updates must happen first so a new place invalidates today's manual cache.
    if command == "/location" or (command not in {"/start", "/help", "/today", "/report", "/wardrobe", "/shop"} and detect_location_update(text)):
        reply = _reply_for(text)
        send_message(chat_id, reply)

        if detect_location_update(text):
            send_message(chat_id, "位置已更新，正在按新地点即时刷新今天的方案。")
            threading.Thread(
                target=deliver_refresh_result,
                args=(chat_id, "today"),
                daemon=True,
            ).start()
        return jsonify({"ok": True, "triggered_refresh": True})

    manual_commands = {"/today": "today", "/report": "report", "/shop": "shop"}
    if command in manual_commands and manual_refresh_needed():
        send_message(chat_id, "收到，正在即时刷新今天的数据和方案；完成后我会直接发给你。")
        threading.Thread(
            target=deliver_refresh_result,
            args=(chat_id, manual_commands[command]),
            daemon=True,
        ).start()
        return jsonify({"ok": True, "triggered_refresh": True})

    # A normal human message also counts as today's first manual request.
    # This lets phrases such as “今天穿什么” trigger preparation without requiring a slash command.
    known_commands = {"/start", "/help", "/today", "/report", "/wardrobe", "/shop", "/location"}
    if text and command not in known_commands and manual_refresh_needed():
        send_message(chat_id, "收到你的当日需求，我先即时刷新今天的数据和方案，完成后直接发给你。")
        threading.Thread(
            target=deliver_refresh_result,
            args=(chat_id, "today"),
            daemon=True,
        ).start()
        return jsonify({"ok": True, "triggered_refresh": True})

    reply = _reply_for(text)
    send_message(chat_id, reply)
    return jsonify({"ok": True, "triggered_refresh": False})


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
