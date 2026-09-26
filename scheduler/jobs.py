import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from curator.trend_curator import build_candidates
from personalizer.monthly_personalizer import update_personal_rules
from research.web_research import collect_daily_signals
from life.daily_planner import build_daily_plan
from life.daily_briefing import render_daily_briefing
from notifications.channel_router import push_message
from life.weather_open_meteo import get_today_weather, get_today_weather_by_coordinates
from life.location_state import get_default_location, get_location_state
from research.learning_report import build_learning_survey, render_learning_survey_md, render_learning_push_summary
from reports.daily_report import build_today_report_file
from notifications.telegram_document import send_document
import yaml

REPORTS = Path("reports")
KNOWLEDGE = Path("knowledge")
PERSONAL = Path("personal")
DATA = Path("data")

for p in (REPORTS, KNOWLEDGE, PERSONAL, DATA):
    p.mkdir(parents=True, exist_ok=True)


def _load_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def daily_life_briefing():
    cfg_path = Path("config/daily_assistant.yaml")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    state = get_location_state()
    location = get_default_location()
    if state.get("latitude") is not None and state.get("longitude") is not None:
        weather = get_today_weather_by_coordinates(
            state["latitude"],
            state["longitude"],
            location=state.get("display_name") or location,
            admin1=state.get("admin1"),
            country=state.get("country") or "中国",
        )
    else:
        weather = get_today_weather(location) if location else None
    plan = build_daily_plan({"weather": weather})
    briefing = render_daily_briefing(plan)
    _write_json(REPORTS / "daily_life_plan.json", plan)
    (REPORTS / "daily_life_briefing.md").write_text(briefing, encoding="utf-8")
    channel = (((cfg or {}).get("delivery") or {}).get("channel", "auto"))
    survey = _load_json(REPORTS / "daily_learning_survey.json", {})
    report_path = build_today_report_file(plan, survey)

    summary_lines = ["今日穿搭与学习日报已生成。"]
    if plan.get("optional_purchase_gap", {}).get("items"):
        top = plan["optional_purchase_gap"]["items"][0]
        summary_lines.append(f"当前优先补充：{top.get('priority')} {top.get('item')}")
    summary_lines.append("完整方案、学习调查和淘宝/拼多多链接见附件。")
    delivery = push_message("\n".join(summary_lines), channel=channel)

    document_delivery = None
    if channel == "telegram":
        document_delivery = send_document(
            report_path,
            caption="今日穿搭与学习报告｜完整方案 + 学习调查 + 采购链接",
        )

    _write_json(REPORTS / "daily_delivery_status.json", {
        "daily_summary": delivery,
        "daily_report_document": document_delivery,
    })
    print(briefing)
    print(json.dumps(delivery, ensure_ascii=False, indent=2))


def daily_light_learning():
    signals = collect_daily_signals()
    candidates = build_candidates()
    survey = build_learning_survey(signals, candidates)
    survey_md = render_learning_survey_md(survey)
    _write_json(REPORTS / "daily_learning_survey.json", survey)
    (REPORTS / "daily_learning_survey.md").write_text(survey_md, encoding="utf-8")

    event = {
        "run_type": "daily_light_learning",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "policy": "collect_only_no_personal_rule_promotion",
        "query_batch_count": len(signals),
        "result_count": sum(len(x.get("results", [])) for x in signals),
        "candidate_rule_count": len(candidates),
        "survey_report": "reports/daily_learning_survey.md",
    }

    _write_json(REPORTS / "daily_learning_latest.json", event)
    print(json.dumps(event, ensure_ascii=False, indent=2))


def weekly_review():
    candidates = build_candidates()
    current = _load_json(KNOWLEDGE / "current_trends.json", [])
    creators = _load_json("research/creators.json", [])
    celebrities = _load_json("research/celebrity_profiles.json", [])

    report = {
        "run_type": "weekly_review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trend_batch_count": len(current),
        "candidate_rule_count": len(candidates),
        "creator_profile_count": len(creators),
        "celebrity_profile_count": len(celebrities),
        "policy": "review_and_score_only_no_personal_rule_promotion",
        "candidate_rules": candidates,
    }

    _write_json(REPORTS / "weekly_style_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def monthly_personal_review():
    before = _load_json(PERSONAL / "learned_rules.json", [])
    updated = update_personal_rules()
    feedback = _load_json(DATA / "feedback.json", [])
    history = _load_json(DATA / "outfit_history.json", [])
    candidates = _load_json(KNOWLEDGE / "candidate_rules.json", [])

    report = {
        "run_type": "monthly_personal_review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "feedback_count": len(feedback),
        "outfit_history_count": len(history),
        "personal_rule_count_before": len(before),
        "personal_rule_count_after": len(updated),
        "candidate_rule_count": len(candidates),
        "policy": "personal_rules_can_be_promoted_or_demoted_here",
        "personal_rules": updated,
    }

    _write_json(REPORTS / "monthly_personal_review.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "job",
        choices=["daily", "daily-briefing", "weekly", "monthly"],
    )
    args = parser.parse_args()

    if args.job == "daily":
        daily_light_learning()
    elif args.job == "daily-briefing":
        daily_life_briefing()
    elif args.job == "weekly":
        weekly_review()
    else:
        monthly_personal_review()


if __name__ == "__main__":
    main()
