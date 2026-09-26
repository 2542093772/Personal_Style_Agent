import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

CREATORS = Path("research/creators.json")
TRENDS = Path("knowledge/current_trends.json")
OUT = Path("research/creator_philosophies.json")

THEMES = {
    "proportion": ["比例", "显高", "显瘦", "腰线", "肩线", "proportion", "silhouette", "leg line"],
    "fit": ["版型", "合身", "宽松", "直筒", "fit", "oversized", "straight fit"],
    "color": ["配色", "中性色", "同色系", "color", "neutral", "contrast"],
    "layering": ["叠穿", "层次", "layer", "layering"],
    "capsule_wardrobe": ["胶囊衣橱", "基础款", "复用", "capsule wardrobe", "wardrobe basics"],
    "smart_casual": ["通勤", "smart casual", "tailoring", "casual tailoring"],
    "shopping_logic": ["购买", "性价比", "材质", "面料", "shopping", "fabric", "quality"],
}


def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_creator_philosophies() -> Dict[str, Any]:
    creators = _load(CREATORS, [])
    signals = _load(TRENDS, [])
    creator_map = {x.get("id"): x for x in creators}
    buckets = defaultdict(lambda: defaultdict(list))

    for batch in signals:
        cid = batch.get("creator_id")
        if not cid:
            continue
        for row in batch.get("results", []) or []:
            if not isinstance(row, dict) or row.get("error"):
                continue
            text = " ".join([
                row.get("title", ""),
                row.get("snippet", ""),
            ]).lower()
            for theme, keywords in THEMES.items():
                if any(k.lower() in text for k in keywords):
                    buckets[cid][theme].append({
                        "title": row.get("title", ""),
                        "url": row.get("url", ""),
                        "snippet": row.get("snippet", "")[:260],
                    })

    profiles = {}
    for cid, creator in creator_map.items():
        theme_rows = buckets.get(cid, {})
        philosophies = []
        for theme, evidence in theme_rows.items():
            philosophies.append({
                "theme": theme,
                "evidence_count": len(evidence),
                "confidence": round(min(0.95, 0.45 + len(evidence) * 0.08), 2),
                "evidence": evidence[:8],
            })

        philosophies.sort(key=lambda x: (-x["evidence_count"], x["theme"]))
        profiles[cid] = {
            "creator_id": cid,
            "creator_name": creator.get("name"),
            "role": creator.get("role"),
            "focus_declared": creator.get("focus", []),
            "philosophies": philosophies,
            "dominant_themes": [x["theme"] for x in philosophies[:4]],
            "evidence_total": sum(x["evidence_count"] for x in philosophies),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    theme_creators = defaultdict(list)
    for cid, profile in profiles.items():
        for row in profile["philosophies"]:
            if row["confidence"] >= 0.61:
                theme_creators[row["theme"]].append(cid)

    consensus = []
    for theme, ids in theme_creators.items():
        if len(ids) >= 2:
            consensus.append({
                "theme": theme,
                "creator_count": len(ids),
                "creator_ids": ids,
                "strength": round(min(1.0, 0.5 + len(ids) * 0.08), 2),
            })
    consensus.sort(key=lambda x: (-x["creator_count"], x["theme"]))

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "creator_count": len(creators),
        "profiled_creator_count": sum(1 for x in profiles.values() if x["evidence_total"] > 0),
        "profiles": profiles,
        "cross_creator_consensus": consensus,
    }
    _save(OUT, output)
    return output
