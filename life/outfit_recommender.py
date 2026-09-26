from typing import Any, Dict, List


CORE_CATEGORIES = ["top", "bottom", "shoes", "outerwear"]


def _text(item: Dict[str, Any]) -> str:
    parts = [
        str(item.get("name", "")),
        str(item.get("title", "")),
        str(item.get("category", "")),
        str(item.get("color", "")),
        " ".join(map(str, item.get("tags", []) or [])),
    ]
    return " ".join(parts).lower()


def internet_style_suggestions(trends: List[Dict[str, Any]], candidate_rules: List[Dict[str, Any]], limit=5):
    suggestions = []

    if isinstance(candidate_rules, list):
        for rule in candidate_rules:
            if not isinstance(rule, dict):
                continue
            title = rule.get("title") or rule.get("rule") or rule.get("name")
            reason = rule.get("reason") or rule.get("rationale") or rule.get("description")
            if title:
                suggestions.append({
                    "title": title,
                    "reason": reason or "来自近期学习候选规则",
                    "source": "candidate_rule",
                    "confidence": rule.get("confidence"),
                })
            if len(suggestions) >= limit:
                return suggestions

    if isinstance(trends, list):
        for batch in trends:
            if not isinstance(batch, dict):
                continue
            query = batch.get("query", "")
            for row in batch.get("results", []) or []:
                if not isinstance(row, dict) or row.get("error"):
                    continue
                title = row.get("title")
                if title:
                    suggestions.append({
                        "title": title,
                        "reason": row.get("snippet", "")[:220],
                        "source": row.get("url", ""),
                        "query": query,
                    })
                if len(suggestions) >= limit:
                    return suggestions
    return suggestions


def wardrobe_outfit(wardrobe: List[Dict[str, Any]], visual_rules: List[Dict[str, Any]]):
    if not isinstance(wardrobe, list) or not wardrobe:
        return {
            "status": "needs_wardrobe_items",
            "items": [],
            "reason": "衣柜数据为空，不能编造现有单品。",
        }

    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for item in wardrobe:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "unknown")).lower()
        by_category.setdefault(category, []).append(item)

    selected = []
    for category in CORE_CATEGORIES:
        items = by_category.get(category, [])
        if not items:
            continue

        best = None
        best_score = -1
        for item in items:
            score = 0
            txt = _text(item)
            if item.get("available", True):
                score += 3
            if item.get("favorite"):
                score += 2

            for rule in visual_rules:
                applies = rule.get("applies_to", []) or []
                if category in applies:
                    score += float(rule.get("confidence", 0.5))
                    title = str(rule.get("title", "")).lower()
                    if any(k in txt for k in ["high waist", "高腰", "clean", "直筒", "简洁"]) and any(
                        k in title for k in ["腰", "纵向", "干净", "轮廓"]
                    ):
                        score += 1

            if score > best_score:
                best_score = score
                best = item

        if best:
            selected.append({
                "category": category,
                "name": best.get("name") or best.get("title") or "未命名单品",
                "score": round(best_score, 2),
                "id": best.get("id"),
            })

    return {
        "status": "ready" if selected else "insufficient_categories",
        "items": selected,
        "reason": "优先从现有衣柜中选择可用、常穿且符合个人比例规则的单品。",
    }


def build_outfit_recommendations(wardrobe, trends, candidate_rules, visual_rules):
    return {
        "internet_recommendation": internet_style_suggestions(trends, candidate_rules),
        "wardrobe_recommendation": wardrobe_outfit(wardrobe, visual_rules),
    }
