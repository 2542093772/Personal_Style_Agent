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
                platform = "淘宝" if c.get("marketplace") == "taobao" else "拼多多"
                price = c.get("price_seen")
                price_text = f"｜抓取价约 ¥{price}" if price else ""
                lines.append(f"- [{platform}] {title}{price_text}\n  {c.get('url')}")
        else:
            lines.append("具体商品：本轮没有抓到可靠的淘宝/拼多多商品详情页，不用搜索页凑数。")

    lines += ["", "链接用于候选筛选；下单前仍需核对尺码、材质、卖家和当前价格。"]
    return "\n".join(lines)
