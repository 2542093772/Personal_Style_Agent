from typing import Dict, Any


def render_daily_briefing(plan: Dict[str, Any]) -> str:
    ctx = plan.get("today_context", {})
    wardrobe = plan.get("wardrobe", {})
    outfit = plan.get("outfit_plan", {})
    rules = plan.get("personal_baseline", {}).get("top_visual_rules", [])

    lines = ["# 今日生活方案", ""]

    weather = ctx.get("weather")
    schedule = ctx.get("schedule")
    if weather:
        lines += [f"天气：{weather}"]
    if schedule:
        lines += [f"日程：{schedule}"]
    if weather or schedule:
        lines.append("")

    lines += ["## 今日穿搭原则"]
    if rules:
        for r in rules[:5]:
            lines.append(f"- {r.get('title')}: {r.get('rationale')}")
    else:
        lines.append("- 继续沿用当前基础偏好；个人档案规则尚不足。")

    lines += ["", "## 衣柜状态"]
    lines.append(f"- 已录入单品：{wardrobe.get('item_count', 0)}")
    if outfit.get("status") == "needs_wardrobe_items":
        lines.append("- 当前衣柜数据为空，今天暂不编造具体单品搭配。")
    else:
        lines.append("- 衣柜已可用于后续自动选款与组合评分。")

    lines += ["", "## 今日提醒"]
    reminders = plan.get("useful_reminders", [])
    if reminders:
        lines.extend([f"- {x}" for x in reminders])
    else:
        lines.append("- 暂无额外提醒。")

    return "\n".join(lines) + "\n"
