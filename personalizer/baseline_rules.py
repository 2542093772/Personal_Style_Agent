from typing import Any, Dict, List


GOAL_RULES = {
    "clean": {
        "title": "保持干净、低复杂度的整体轮廓",
        "rationale": "减少多余装饰和杂乱层次，优先清晰线条与中性色。",
        "priority": 90,
        "confidence": 1.0,
    },
    "youthful": {
        "title": "避免显老：优先轻量、利落、不过度正式",
        "rationale": "用简洁休闲轮廓代替厚重或过度商务化的组合。",
        "priority": 95,
        "confidence": 1.0,
    },
    "sharp": {
        "title": "保持利落感：肩线、裤线、鞋型尽量干净",
        "rationale": "通过清楚的结构边界提高整体精致度。",
        "priority": 85,
        "confidence": 1.0,
    },
}

AVOID_RULES = {
    "looks_older": {
        "title": "避免成熟感过重的搭配",
        "rationale": "减少老气配色、厚重商务单品和过度正式组合。",
        "priority": 100,
        "confidence": 1.0,
    },
    "looks_heavier": {
        "title": "避免横向膨胀和上身过厚",
        "rationale": "优先纵向线条、合适衣长和不过度堆叠的上装。",
        "priority": 100,
        "confidence": 1.0,
    },
    "greasy": {
        "title": "避免油腻感：控制装饰、Logo 和高光材质",
        "rationale": "保持克制、干净和年轻感。",
        "priority": 90,
        "confidence": 1.0,
    },
    "top_heavy": {
        "title": "避免上重下轻",
        "rationale": "减少厚重上装和过度宽肩视觉，保持上下比例平衡。",
        "priority": 95,
        "confidence": 1.0,
    },
}


def build_baseline_rules(profile_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    rules = []
    for goal in profile_cfg.get("goals", []) or []:
        if goal in GOAL_RULES:
            row = dict(GOAL_RULES[goal])
            row["source"] = "profile_goal"
            rules.append(row)

    for avoid in profile_cfg.get("avoid", []) or []:
        if avoid in AVOID_RULES:
            row = dict(AVOID_RULES[avoid])
            row["source"] = "profile_avoid"
            rules.append(row)

    rules.sort(key=lambda r: -int(r.get("priority", 0)))
    return rules
