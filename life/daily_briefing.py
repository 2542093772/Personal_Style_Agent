from typing import Dict, Any


def render_daily_briefing(plan: Dict[str, Any]) -> str:
    ctx = plan.get("today_context", {})
    outfit = plan.get("outfit_plan", {})
    internet = outfit.get("internet_recommendation", []) or []
    wardrobe = outfit.get("wardrobe_recommendation", {}) or {}
    rules = plan.get("personal_baseline", {}).get("top_visual_rules", [])

    lines = ["# 今日生活方案", ""]

    weather = ctx.get("weather")
    schedule = ctx.get("schedule")
    if weather:
        lines.append(f"天气：{weather}")
    if schedule:
        lines.append(f"日程：{schedule}")
    if weather or schedule:
        lines.append("")

    lines += ["## 互联网学习后的建议穿搭"]
    if internet:
        for idx, item in enumerate(internet[:3], 1):
            lines.append(f"{idx}. {item.get('title', '建议方案')}")
            formula = item.get("formula") or []
            if formula:
                lines.append("   组合：" + " + ".join(map(str, formula)))
            if item.get("reason"):
                lines.append(f"   原因：{item.get('reason')}")
            if item.get("evidence_count") is not None:
                lines.append(f"   学习证据数：{item.get('evidence_count')}")
    else:
        lines.append("- 今日暂无足够的互联网学习信号形成可靠方案。")

    lines += ["", "## 你现有衣柜今天可直接穿"]
    items = wardrobe.get("items", []) or []
    if items:
        for item in items:
            lines.append(f"- {item.get('category')}: {item.get('name')}")
        if wardrobe.get("reason"):
            lines.append(f"- 选择逻辑：{wardrobe.get('reason')}")
    else:
        lines.append(f"- {wardrobe.get('reason', '衣柜数据不足，暂不编造具体单品。')}")

    lines += ["", "## 个人比例规则"]
    if rules:
        for r in rules[:4]:
            lines.append(f"- {r.get('title')}")
    else:
        lines.append("- 暂无稳定视觉规则。")

    purchase = plan.get("optional_purchase_gap", {}) or {}
    purchase_items = purchase.get("items", []) or []
    lines += ["", "## 当前最值得补的单品"]
    if purchase_items:
        for item in purchase_items[:2]:
            lines.append(f"- {item.get('priority')}: {item.get('item')}")
            if item.get("why"):
                lines.append(f"  原因：{item.get('why')}")
            candidates = item.get("live_candidates", []) or []
            if candidates:
                first = candidates[0]
                platform = "淘宝" if first.get("marketplace") == "taobao" else "拼多多"
                lines.append(f"  具体商品：[{platform}] {first.get('title')}")
                lines.append(f"  链接：{first.get('url')}")
            else:
                lines.append("  具体商品：本轮未找到可靠详情页，不推泛搜索链接。")
        lines.append("- 更多候选可在 Telegram 输入 /shop")
    else:
        lines.append("- 当前暂无核心采购缺口。")

    lines += ["", "## 今日提醒"]
    reminders = plan.get("useful_reminders", [])
    if reminders:
        lines.extend([f"- {x}" for x in reminders])
    else:
        lines.append("- 暂无额外提醒。")

    return "\n".join(lines) + "\n"
