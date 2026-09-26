import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

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


def daily_light_learning():
    current = _load_json(KNOWLEDGE / "current_trends.json", [])
    candidates = _load_json(KNOWLEDGE / "candidate_rules.json", [])

    event = {
        "run_type": "daily_light_learning",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "policy": "collect_only_no_personal_rule_promotion",
        "trend_count_before": len(current),
        "candidate_count_before": len(candidates),
    }

    _write_json(REPORTS / "daily_learning_latest.json", event)
    print(json.dumps(event, ensure_ascii=False, indent=2))


def weekly_review():
    current = _load_json(KNOWLEDGE / "current_trends.json", [])
    candidates = _load_json(KNOWLEDGE / "candidate_rules.json", [])
    creators = _load_json("research/creators.json", [])
    celebrities = _load_json("research/celebrity_profiles.json", [])

    report = {
        "run_type": "weekly_review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trend_signal_count": len(current),
        "candidate_rule_count": len(candidates),
        "creator_profile_count": len(creators),
        "celebrity_profile_count": len(celebrities),
        "policy": "review_and_score_only_no_personal_rule_promotion",
    }

    _write_json(REPORTS / "weekly_style_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def monthly_personal_review():
    feedback = _load_json(DATA / "feedback.json", [])
    history = _load_json(DATA / "outfit_history.json", [])
    learned = _load_json(PERSONAL / "learned_rules.json", [])
    candidates = _load_json(KNOWLEDGE / "candidate_rules.json", [])

    report = {
        "run_type": "monthly_personal_review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "feedback_count": len(feedback),
        "outfit_history_count": len(history),
        "existing_personal_rule_count": len(learned),
        "candidate_rule_count": len(candidates),
        "policy": "personal_rules_can_be_promoted_or_demoted_here",
    }

    _write_json(REPORTS / "monthly_personal_review.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "job",
        choices=["daily", "weekly", "monthly"],
    )
    args = parser.parse_args()

    if args.job == "daily":
        daily_light_learning()
    elif args.job == "weekly":
        weekly_review()
    else:
        monthly_personal_review()


if __name__ == "__main__":
    main()
