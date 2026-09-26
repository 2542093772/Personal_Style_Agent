from datetime import datetime, timezone
from typing import Any, Dict, List


def build_learning_survey(signals: List[Dict[str, Any]], candidate_rules: List[Dict[str, Any]] | None = None):
    candidate_rules = candidate_rules or []
    sources = []
    errors = []

    for batch in signals or []:
        query = batch.get("query", "") if isinstance(batch, dict) else ""
        for row in (batch.get("results", []) if isinstance(batch, dict) else []) or []:
            if not isinstance(row, dict):
                continue
            if row.get("error"):
                errors.append({"query": query, "error": row.get("error")})
                continue
            if row.get("title") or row.get("url"):
                sources.append({
                    "query": query,
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "snippet": row.get("snippet", "")[:260],
                })

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_count": len(signals or []),
        "source_count": len(sources),
        "error_count": len(errors),
        "sources": sources[:30],
        "candidate_rules": candidate_rules[:20] if isinstance(candidate_rules, list) else [],
        "errors": errors[:10],
        "policy": {
            "daily_learning_is_observation_only": True,
            "personal_rules_are_not_overwritten_directly": True,
            "promotion_requires_review": True,
        },
    }


def render_learning_survey_md(report: Dict[str, Any]) -> str:
    lines = [
        "# 每日学习调查报告",
        "",
        f"- 检索主题：{report.get('query_count', 0)}",
        f"- 有效来源：{report.get('source_count', 0)}",
        f"- 检索异常：{report.get('error_count', 0)}",
        "",
        "## 今日来源",
    ]

    sources = report.get("sources", [])
    if not sources:
        lines.append("- 今日暂无有效公开来源。")
    else:
        for row in sources[:15]:
            title = row.get("title") or "未命名来源"
            url = row.get("url") or ""
            query = row.get("query") or ""
            lines.append(f"- {title}｜检索：{query}")
            if url:
                lines.append(f"  {url}")
            if row.get("snippet"):
                lines.append(f"  摘要：{row.get('snippet')}")

    lines += ["", "## 候选穿搭规则"]
    rules = report.get("candidate_rules", [])
    if not rules:
        lines.append("- 暂无新的候选规则。")
    else:
        for rule in rules[:10]:
            if isinstance(rule, dict):
                title = rule.get("title") or rule.get("rule") or rule.get("name") or str(rule)
                lines.append(f"- {title}")
            else:
                lines.append(f"- {rule}")

    lines += [
        "",
        "## 学习边界",
        "- 每日学习只收集与整理信号，不直接覆盖你的个人穿搭规则。",
        "- 候选规则需要后续复核和个人反馈后才进入长期规则。",
    ]
    return "\n".join(lines) + "\n"
