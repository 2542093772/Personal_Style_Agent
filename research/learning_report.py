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
    session = report.get("learning_session", {}) or {}
    lines = [
        "# 每日学习调查报告",
        "",
        f"- 检索主题：{report.get('query_count', 0)}",
        f"- 有效来源：{report.get('source_count', 0)}",
        f"- 检索异常：{report.get('error_count', 0)}",
    ]
    if session:
        elapsed_min = round(float(session.get("actual_elapsed_seconds", 0)) / 60, 1)
        lines += [
            f"- 持续学习：{elapsed_min} 分钟",
            f"- 学习轮次：{session.get('rounds', 0)}",
            f"- 去重后来源：{session.get('unique_result_count', 0)}",
        ]
    lines += [
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


def render_learning_push_summary(report: Dict[str, Any]) -> str:
    session = report.get("learning_session", {}) or {}
    session_text = ""
    if session:
        elapsed_min = round(float(session.get("actual_elapsed_seconds", 0)) / 60, 1)
        session_text = f" ｜ 学习 {elapsed_min} 分钟 / {session.get('rounds', 0)} 轮"
    lines = [
        "# 今日学习调查摘要",
        f"检索主题：{report.get('query_count', 0)} ｜ 有效来源：{report.get('source_count', 0)} ｜ 候选规则：{len(report.get('candidate_rules', []) or [])}{session_text}",
        "",
    ]
    sources = report.get("sources", []) or []
    if sources:
        lines.append("重点来源：")
        for row in sources[:5]:
            title = row.get("title") or "未命名来源"
            lines.append(f"- {title}")
    else:
        lines.append("今日暂无有效公开来源。")

    rules = report.get("candidate_rules", []) or []
    if rules:
        lines.append("")
        lines.append("今日候选方向：")
        for rule in rules[:4]:
            if isinstance(rule, dict):
                name = rule.get("title") or rule.get("rule_type") or rule.get("rule") or "候选规则"
                evidence = rule.get("evidence_count")
                suffix = f"（证据 {evidence}）" if evidence is not None else ""
                lines.append(f"- {name}{suffix}")

    lines += ["", "完整报告已保存到 reports/daily_learning_survey.md"]
    return "\n".join(lines)
