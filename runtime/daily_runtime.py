import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml

from curator.trend_curator import build_candidates
from life.daily_planner import build_daily_plan
from life.weather_open_meteo import get_today_weather
from life.location_state import get_default_location
from research.learning_report import build_learning_survey
from research.web_research import collect_daily_signals

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)


def _json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _yaml(path: Path, default):
    if not path.exists():
        return default
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or default
    except Exception:
        return default


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _survey_is_today(survey: Dict[str, Any]) -> bool:
    stamp = str(survey.get("generated_at_utc", ""))
    return stamp.startswith(_today_utc())


def ensure_learning(force: bool = False) -> Dict[str, Any]:
    survey_path = REPORTS / "daily_learning_survey.json"
    survey = _json(survey_path, {})
    if survey and _survey_is_today(survey) and not force:
        return survey

    try:
        signals = collect_daily_signals()
        candidates = build_candidates()
        survey = build_learning_survey(signals, candidates)
        survey_path.write_text(json.dumps(survey, ensure_ascii=False, indent=2), encoding="utf-8")
        return survey
    except Exception as exc:
        # Never make the entire daily assistant fail just because internet research failed.
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "query_count": 0,
            "source_count": 0,
            "candidate_rules": [],
            "sources": [],
            "runtime_error": str(exc),
        }


def resolve_location() -> str:
    return get_default_location()


def ensure_weather() -> Dict[str, Any] | None:
    location = resolve_location()
    if not location:
        return None
    try:
        return get_today_weather(location)
    except Exception as exc:
        return {"ok": False, "location": location, "error": str(exc)}


def build_runtime_bundle(force_learning: bool = False):
    survey = ensure_learning(force=force_learning)
    weather = ensure_weather()
    plan = build_daily_plan({"weather": weather})
    return {
        "survey": survey,
        "weather": weather,
        "plan": plan,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
