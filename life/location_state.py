import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "personal" / "location_state.json"
CONFIG_PATH = ROOT / "config" / "daily_assistant.yaml"

DEFAULT_LOCATION = "Suzhou"
DEFAULT_DISPLAY_NAME = "苏州"

CITY_ALIASES = {
    "苏州": {"query": "Suzhou", "admin1": "Jiangsu"},
    "上海": {"query": "Shanghai", "admin1": "Shanghai"},
    "泰州": {"query": "Taizhou", "admin1": "Jiangsu"},
    "杭州": {"query": "Hangzhou", "admin1": "Zhejiang"},
    "南京": {"query": "Nanjing", "admin1": "Jiangsu"},
    "北京": {"query": "Beijing", "admin1": "Beijing"},
    "深圳": {"query": "Shenzhen", "admin1": "Guangdong"},
    "广州": {"query": "Guangzhou", "admin1": "Guangdong"},
    "宁波": {"query": "Ningbo", "admin1": "Zhejiang"},
}

TRAVEL_PATTERNS = [
    r"(?:我)?(?:现在|目前|这几天|接下来|之后)?(?:在|到了|到|住在|待在)\s*([A-Za-z\u4e00-\u9fff·]{2,16}?)(?:了|出差|旅游|工作|待|住|，|。|！|!|$)",
    r"(?:我)?(?:明天|后天|今天|准备|计划|要|会)?(?:去|前往|回)\s*([A-Za-z\u4e00-\u9fff·]{2,16}?)(?:了|出差|旅游|工作|待|住|，|。|！|!|$)",
    r"(?:默认地点|常驻地点|所在地|位置)\s*(?:改成|改为|设置为|设置成|是|：|:)\s*([A-Za-z\u4e00-\u9fff·]{2,16})",
]


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_state(state: Dict[str, Any]):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _config_fallback() -> str:
    try:
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return str(((cfg.get("weather") or {}).get("location") or DEFAULT_LOCATION)).strip()
    except Exception:
        return DEFAULT_LOCATION


def get_location_state() -> Dict[str, Any]:
    state = _read_json(STATE_PATH, {})
    if not state:
        state = {
            "default_location": _config_fallback(),
            "display_name": DEFAULT_DISPLAY_NAME,
            "source": "default",
            "updated_at_utc": None,
        }
    return state


def get_default_location() -> str:
    env_location = os.getenv("LIFE_ASSISTANT_LOCATION", "").strip()
    if env_location:
        return env_location
    state = get_location_state()
    return str(state.get("default_location") or _config_fallback()).strip()


def geocode_location(name: str) -> Optional[Dict[str, Any]]:
    name = (name or "").strip()
    if not name:
        return None

    alias = CITY_ALIASES.get(name)
    query_name = alias.get("query") if alias else name
    preferred_admin1 = (alias or {}).get("admin1")

    q = urllib.parse.urlencode({
        "name": query_name,
        "count": 10,
        "language": "zh",
        "format": "json",
    })
    url = f"https://geocoding-api.open-meteo.com/v1/search?{q}"
    try:
        with urllib.request.urlopen(url, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    rows = data.get("results") or []
    if not rows:
        return None

    row = rows[0]
    if preferred_admin1:
        preferred = preferred_admin1.lower()
        for candidate in rows:
            admin1 = str(candidate.get("admin1") or "").lower()
            if preferred in admin1 or admin1 in preferred:
                row = candidate
                break

    return {
        "query": name,
        "default_location": row.get("name") or query_name,
        "display_name": name if alias else (row.get("name") or name),
        "admin1": row.get("admin1"),
        "country": row.get("country"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
    }


def detect_location_update(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None

    if text.lower().startswith("/location"):
        candidate = text[len("/location"):].strip()
        return geocode_location(candidate) if candidate else None

    for pattern in TRAVEL_PATTERNS:
        m = re.search(pattern, text)
        if not m:
            continue
        candidate = m.group(1).strip()
        resolved = geocode_location(candidate)
        if resolved:
            return resolved
    return None


def _github_repo() -> str:
    return os.getenv("LOCATION_STATE_GITHUB_REPO", "2542093772/Personal_Style_Agent").strip()


def _persist_to_github(state: Dict[str, Any]) -> Dict[str, Any]:
    token = os.getenv("GITHUB_LOCATION_TOKEN", "").strip()
    if not token:
        return {"ok": False, "reason": "GITHUB_LOCATION_TOKEN not configured"}

    repo = _github_repo()
    api = f"https://api.github.com/repos/{repo}/contents/personal/location_state.json"
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
            return {"ok": False, "reason": f"GitHub read failed: {exc}"}
    except Exception as exc:
        return {"ok": False, "reason": f"GitHub read failed: {exc}"}

    payload = {
        "message": f"chore: update default location to {state.get('display_name')}",
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
        return {"ok": False, "reason": f"GitHub write failed: {exc}"}


def update_default_location(resolved: Dict[str, Any], source_text: str = "") -> Dict[str, Any]:
    state = {
        "default_location": resolved.get("default_location") or resolved.get("query"),
        "display_name": resolved.get("display_name") or resolved.get("query"),
        "admin1": resolved.get("admin1"),
        "country": resolved.get("country"),
        "latitude": resolved.get("latitude"),
        "longitude": resolved.get("longitude"),
        "source": "telegram_message",
        "source_text": source_text[:200],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_state(state)
    persistence = _persist_to_github(state)
    return {"state": state, "persistence": persistence}
