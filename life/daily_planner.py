import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from life.outfit_recommender import build_outfit_recommendations
from shopping.ideal_wardrobe import build_purchase_advice
from personalizer.baseline_rules import build_baseline_rules
from life.context_rules import weather_actions, weather_summary

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str, default):
    p = ROOT / path
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _yaml(path: str, default):
    p = ROOT / path
    if not p.exists():
        return default
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or default
    except Exception:
        return default


def _recent(items, n=5):
    if not isinstance(items, list):
        return []
    return items[-n:]


def _wardrobe_summary(items: List[Dict[str, Any]]):
    counts: Dict[str, int] = {}
    for item in items:
        category = item.get("category", "unknown")
        counts[category] = counts.get(category, 0) + 1
    return counts


def _top_visual_rules(rule_doc: Dict[str, Any], limit=5):
    rules = rule_doc.get("rules", []) if isinstance(rule_doc, dict) else []
    return sorted(
        rules,
        key=lambda r: (-int(r.get("priority", 0)), -float(r.get("confidence", 0))),
    )[:limit]


def build_daily_plan(context: Dict[str, Any] | None = None):
    context = context or {}
    config = _yaml("config/daily_assistant.yaml", {})
    profile = _json("personal/visual_profile.json", {})
    visual_rules = _json("personal/visual_style_rules.json", {})
    profile_cfg = _yaml("config/profile.yaml", {})
    learned_rules = _json("personal/learned_rules.json", [])
    wardrobe = _json("data/wardrobe.json", [])
    feedback = _json("data/feedback.json", [])
    candidate_rules = _json("knowledge/candidate_rules.json", [])
    trends = _json("knowledge/current_trends.json", [])

    stable = profile.get("stable_profile", {})
    top_rules = _top_visual_rules(visual_rules)
    if not top_rules:
        top_rules = build_baseline_rules(profile_cfg)[:5]

    outfit_recommendations = build_outfit_recommendations(
        wardrobe if isinstance(wardrobe, list) else [],
        trends if isinstance(trends, list) else [],
        candidate_rules if isinstance(candidate_rules, list) else [],
        top_rules,
    )

    purchase_advice = build_purchase_advice(include_live_links=True, limit=3)

    plan = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "assistant_mode": "daily_life_assistant",
        "profile_policy": {
            "reuse_existing_profile": True,
            "profile_sample_count": stable.get("sample_count", 0),
        },
        "today_context": {
            "weather": context.get("weather"),
            "weather_summary": weather_summary(context.get("weather")),
            "schedule": context.get("schedule"),
            "occasion": context.get("occasion", "daily"),
            "notes": context.get("notes", []),
        },
        "personal_baseline": {
            "stable_profile": stable,
            "top_visual_rules": top_rules,
            "learned_rule_count": len(learned_rules) if isinstance(learned_rules, list) else 0,
        },
        "wardrobe": {
            "item_count": len(wardrobe) if isinstance(wardrobe, list) else 0,
            "category_counts": _wardrobe_summary(wardrobe if isinstance(wardrobe, list) else []),
        },
        "recent_feedback": _recent(feedback, 5),
        "style_learning": {
            "candidate_rules": _recent(candidate_rules, 5),
            "trend_batches": _recent(trends, 3),
        },
        "outfit_plan": {
            "principles": [r.get("title") for r in top_rules],
            "internet_recommendation": outfit_recommendations.get("internet_recommendation", []),
            "wardrobe_recommendation": outfit_recommendations.get("wardrobe_recommendation", {}),
        },
        "grooming": {
            "status": "use_existing_profile",
            "notes": [],
        },
        "useful_reminders": weather_actions(context.get("weather")),
        "optional_purchase_gap": {
            "should_buy": bool(purchase_advice),
            "reason": "Current wardrobe is sparse; recommendations are generated only for identified capsule-wardrobe gaps." if purchase_advice else "No core wardrobe gap identified.",
            "items": purchase_advice,
        },
    }

    return plan
