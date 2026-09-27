import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from research.creator_philosophy import build_creator_philosophies
from research.creator_discovery import discover_creator_candidates, promote_qualified_candidates
import yaml

REPORTS = ROOT / "reports"
KNOWLEDGE = ROOT / "knowledge"
PERSONAL = ROOT / "personal"
DATA = ROOT / "data"

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
    cfg_path = ROOT / "config" / "daily_assistant.yaml"
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


def _signal_identity(batch, row):
    return (
        str(batch.get("creator_id") or ""),
        str(batch.get("query") or ""),
        str(row.get("url") or ""),
        str(row.get("title") or ""),
    )


def _merge_signal_batches(accumulated, new_batches):
    by_batch = {}

    for batch in accumulated:
        key = (
            batch.get("source_type", "generic"),
            batch.get("creator_id"),
            batch.get("query"),
        )
        clone = dict(batch)
        clone["results"] = list(batch.get("results", []) or [])
        by_batch[key] = clone

    for batch in new_batches:
        key = (
            batch.get("source_type", "generic"),
            batch.get("creator_id"),
            batch.get("query"),
        )
        target = by_batch.setdefault(key, {**batch, "results": []})
        seen = {
            _signal_identity(target, row)
            for row in target.get("results", [])
            if isinstance(row, dict) and not row.get("error")
        }
        for row in batch.get("results", []) or []:
            if not isinstance(row, dict):
                continue
            if row.get("error"):
                if not target.get("results"):
                    target["results"].append(row)
                continue
            identity = _signal_identity(batch, row)
            if identity in seen:
                continue
            target["results"].append(row)
            seen.add(identity)

        target["last_collected_at_utc"] = batch.get("collected_at_utc")

    return list(by_batch.values())


def daily_light_learning():
    minimum_minutes = max(1, int(os.getenv("DAILY_LEARNING_MINUTES", "30")))
    round_interval = max(60, int(os.getenv("DAILY_LEARNING_ROUND_INTERVAL_SECONDS", "240")))
    started = time.monotonic()
    deadline = started + minimum_minutes * 60
    accumulated = []
    rounds = 0
    candidates = []
    philosophies = {}

    while True:
        rounds += 1
        round_started = datetime.now(timezone.utc).isoformat()

        fresh = collect_daily_signals()
        accumulated = _merge_signal_batches(accumulated, fresh)

        # Persist the full session before curation so rules/philosophies see
        # all unique evidence collected tonight, not only the latest round.
        _write_json(KNOWLEDGE / "current_trends.json", accumulated)

        if rounds == 1 or rounds % 2 == 0:
            try:
                discover_creator_candidates()
            except Exception:
                pass

        candidates = build_candidates()
        philosophies = build_creator_philosophies()

        elapsed_seconds = int(time.monotonic() - started)
        progress = {
            "run_type": "daily_learning_session",
            "status": "running",
            "round": rounds,
            "minimum_minutes": minimum_minutes,
            "elapsed_seconds": elapsed_seconds,
            "unique_query_batches": len(accumulated),
            "unique_result_count": sum(
                len([r for r in x.get("results", []) if isinstance(r, dict) and not r.get("error")])
                for x in accumulated
            ),
            "profiled_creator_count": philosophies.get("profiled_creator_count", 0),
            "round_started_at_utc": round_started,
        }
        _write_json(REPORTS / "daily_learning_progress.json", progress)
        print(json.dumps(progress, ensure_ascii=False, indent=2), flush=True)

        now = time.monotonic()
        if now >= deadline:
            break

        time.sleep(min(round_interval, max(1, int(deadline - now))))

    survey = build_learning_survey(accumulated, candidates)
    survey["learning_session"] = {
        "minimum_minutes": minimum_minutes,
        "actual_elapsed_seconds": int(time.monotonic() - started),
        "rounds": rounds,
        "unique_query_batches": len(accumulated),
        "unique_result_count": sum(
            len([r for r in x.get("results", []) if isinstance(r, dict) and not r.get("error")])
            for x in accumulated
        ),
    }
    survey_md = render_learning_survey_md(survey)
    _write_json(REPORTS / "daily_learning_survey.json", survey)
    (REPORTS / "daily_learning_survey.md").write_text(survey_md, encoding="utf-8")

    event = {
        "run_type": "daily_learning_session",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "policy": "collect_only_no_personal_rule_promotion",
        "minimum_learning_minutes": minimum_minutes,
        "actual_elapsed_seconds": int(time.monotonic() - started),
        "learning_rounds": rounds,
        "query_batch_count": len(accumulated),
        "result_count": survey["learning_session"]["unique_result_count"],
        "candidate_rule_count": len(candidates),
        "creator_count": philosophies.get("creator_count", 0),
        "profiled_creator_count": philosophies.get("profiled_creator_count", 0),
        "cross_creator_consensus_count": len(philosophies.get("cross_creator_consensus", [])),
        "survey_report": "reports/daily_learning_survey.md",
    }

    _write_json(REPORTS / "daily_learning_progress.json", {**event, "status": "completed"})
    _write_json(REPORTS / "daily_learning_latest.json", event)
    print(json.dumps(event, ensure_ascii=False, indent=2), flush=True)


def weekly_review():
    discovered = discover_creator_candidates()
    promoted = promote_qualified_candidates(max_new=3)
    candidates = build_candidates()
    philosophies = build_creator_philosophies()
    current = _load_json(KNOWLEDGE / "current_trends.json", [])
    creators = _load_json(ROOT / "research" / "creators.json", [])
    celebrities = _load_json(ROOT / "research" / "celebrity_profiles.json", [])

    report = {
        "run_type": "weekly_review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trend_batch_count": len(current),
        "candidate_rule_count": len(candidates),
        "creator_profile_count": len(creators),
        "creator_candidate_count": len(discovered),
        "new_creator_count": len(promoted),
        "profiled_creator_count": philosophies.get("profiled_creator_count", 0),
        "cross_creator_consensus_count": len(philosophies.get("cross_creator_consensus", [])),
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
