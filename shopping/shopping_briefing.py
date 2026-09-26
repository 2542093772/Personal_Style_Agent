from typing import Any, Dict, List


def render_purchase_advice(items: List[Dict[str, Any]], max_items=3) -> str:
    if not items:
        return "当前没有识别到必须补充的核心衣橱缺口。"

    lines = ["🛍 采购优先级"]
    for item in items[:max_items]:
        lines += [
            "",
            f"{item.get('priority', '')}｜{item.get('item', '')}",
            f"为什么：{item.get('why', '')}",
            f"预计可覆盖：约 {item.get('estimated_outfits', '?')} 套组合",
        ]

        notes = item.get("fit_notes", []) or []
        if notes:
            lines.append("版型要点：" + " / ".join(notes[:4]))

        candidates = item.get("live_candidates", []) or []
        if candidates:
            lines.append("候选链接：")
            for c in candidates[:3]:
                title = (c.get("title") or "商品候选").strip()
                lines.append(f"- {title}\n  {c.get('url')}")
        else:
            links = item.get("marketplace_links", {}) or {}
            if links:
                lines.append("搜索链接：")
                for name, url in list(links.items())[:3]:
                    if url:
                        lines.append(f"- {name}: {url}")

    lines += ["", "链接用于候选筛选；下单前仍需核对尺码、材质、卖家和当前价格。"]
    return "\n".join(lines)
