import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from shopping.product_search import build_marketplace_search_url, search_products

ROOT = Path(__file__).resolve().parents[1]


def load_ideal_wardrobe() -> Dict[str, Any]:
    path = ROOT / "config" / "ideal_wardrobe.yaml"
    if not path.exists():
        return {"priorities": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"priorities": []}


def load_current_wardrobe() -> List[Dict[str, Any]]:
    path = ROOT / "data" / "wardrobe.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def wardrobe_gap_plan(limit=5) -> List[Dict[str, Any]]:
    cfg = load_ideal_wardrobe()
    current = load_current_wardrobe()

    category_counts = {}
    for item in current:
        category = str(item.get("category", "")).lower()
        category_counts[category] = category_counts.get(category, 0) + 1

    rows = []
    for item in cfg.get("priorities", []):
        category = str(item.get("category", "")).lower()
        target = int(item.get("target_count", 1))
        have = category_counts.get(category, 0)
        # Near-empty wardrobe policy: category-level coverage first.
        if have >= target:
            continue
        row = dict(item)
        row["current_count"] = have
        row["missing_count"] = max(0, target - have)
        row["marketplace_links"] = {
            "淘宝搜索": build_marketplace_search_url(item.get("search_query", ""), "taobao"),
            "拼多多搜索": build_marketplace_search_url(item.get("search_query", ""), "pinduoduo"),
        }
        rows.append(row)

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    rows.sort(key=lambda x: (order.get(x.get("priority"), 9), x.get("id", "")))
    return rows[:limit]


def live_candidates(gap_item: Dict[str, Any], per_market=2) -> List[Dict[str, Any]]:
    query = gap_item.get("search_query", "")
    results = []
    for market in ("taobao", "pinduoduo"):
        try:
            for row in search_products(query, marketplace=market, max_results=per_market):
                if row.get("url"):
                    results.append(row)
        except Exception:
            continue
    return results[:4]


def build_purchase_advice(include_live_links=False, limit=3):
    gaps = wardrobe_gap_plan(limit=limit)
    output = []
    for gap in gaps:
        row = dict(gap)
        if include_live_links:
            row["live_candidates"] = live_candidates(gap)
        output.append(row)
    return output
