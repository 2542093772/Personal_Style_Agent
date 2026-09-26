import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from zoneinfo import ZoneInfo

from life.daily_briefing import render_daily_briefing
from notifications.telegram_document import send_document
from reports.daily_report import build_today_report_file
from runtime.daily_runtime import build_runtime_bundle

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "personal" / "manual_trigger_state.json"
REPORTS = ROOT / "reports"
TZ = ZoneInfo("Asia/Shanghai")


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _today_local() -> str:
    return datetime.now(TZ).date().isoformat()


def _context_key() -> str:
    location = _read_json(ROOT / "personal" / "location_state.json", {})
    payload = {
        "date": _today_local(),
        "default_location": location.get("default_location"),
        "display_name": location.get("display_name"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "location_updated_at": location.get("updated_at_utc"),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def _github_token() -> str:
    return (
        os.getenv("GITHUB_STATE_TOKEN", "").strip()
        or os.getenv("GITHUB_LOCATION_TOKEN", "").strip()
    )


def _persist_state_to_github(state: Dict[str, Any]):
    token = _github_token()
    if not token:
        return {"ok": False, "reason": "GitHub state token not configured"}

    repo = os.getenv(
        "LOCATION_STATE_GITHUB_REPO",
        "2542093772/Personal_Style_Agent",
    ).strip()
    path = "personal/manual_trigger_state.json"
    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Personal-Style-Agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    sha = None
    try:
        req = urllib.request.Request(api + "?ref=main", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            current = json.loads(resp.read().decode("utf-8"))
            sha = current.get("sha")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            return {"ok": False, "reason": str(exc)}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}

    payload = {
        "message": f"chore: record manual daily refresh {_today_local()}",
        "content": base64.b64encode(
            json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    try:
        req = urllib.request.Request(
            api,
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "commit": (result.get("commit") or {}).get("sha")}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}


def manual_refresh_needed() -> bool:
    state = _read_json(STATE_PATH, {})
    return not (
        state.get("local_date") == _today_local()
        and state.get("context_key") == _context_key()
        and state.get("status") == "completed"
    )


def mark_manual_refresh_started(reason: str):
    state = {
        "local_date": _today_local(),
        "context_key": _context_key(),
        "status": "running",
        "reason": reason,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(STATE_PATH, state)
    return state


def refresh_today(reason: str = "human_request"):
    mark_manual_refresh_started(reason)

    bundle = build_runtime_bundle(force_learning=True)
    plan = bundle["plan"]
    survey = bundle["survey"]

    _write_json(REPORTS / "daily_life_plan.json", plan)
    _write_json(REPORTS / "daily_learning_survey.json", survey)
    (REPORTS / "daily_life_briefing.md").write_text(
        render_daily_briefing(plan),
        encoding="utf-8",
    )
    report_path = build_today_report_file(plan, survey)

    state = {
        "local_date": _today_local(),
        "context_key": _context_key(),
        "status": "completed",
        "reason": reason,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_path": "reports/daily_style_report.html",
    }
    _write_json(STATE_PATH, state)
    state["persistence"] = _persist_state_to_github(state)

    return {
        "bundle": bundle,
        "report_path": report_path,
        "state": state,
    }


def deliver_refresh_result(chat_id: str, requested: str = "today"):
    from telegram_bot.bot import send_message
    from shopping.shopping_briefing import render_purchase_advice

    try:
        result = refresh_today(reason=f"telegram:{requested}")
        plan = result["bundle"]["plan"]

        if requested == "report":
            send_document(
                result["report_path"],
                caption="已按你刚才的请求即时刷新：今日穿搭与学习报告",
            )
            send_message(chat_id, "已完成当日即时刷新，并发送最新日报。")
        elif requested == "shop":
            items = (plan.get("optional_purchase_gap") or {}).get("items", [])
            send_message(chat_id, render_purchase_advice(items))
        else:
            send_message(chat_id, render_daily_briefing(plan))
    except Exception as exc:
        send_message(chat_id, f"当日即时刷新失败：{exc}")
