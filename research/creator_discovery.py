import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ddgs import DDGS

CREATORS = Path("research/creators.json")
CANDIDATES = Path("research/creator_candidates.json")

DISCOVERY_QUERIES = [
    "优秀 男装 穿搭 博主 比例 版型 B站",
    "男生 穿搭 博主 胶囊衣橱 小红书",
    "menswear creator outfit proportions YouTube",
    "menswear capsule wardrobe creator Instagram",
]

CREATOR_PATTERNS = [
    re.compile(r"([A-Za-z][A-Za-z0-9 ._'&/-]{2,40})"),
    re.compile(r"([\u4e00-\u9fffA-Za-z0-9·_-]{2,24})"),
]


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


def _search(query: str, max_results=10):
    rows = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            rows.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })
    return rows


def _candidate_key(name: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", name.lower()).strip("_")[:64]


def discover_creator_candidates() -> List[Dict[str, Any]]:
    existing = _load(CREATORS, [])
    existing_names = {str(x.get("name", "")).lower() for x in existing}
    existing_ids = {x.get("id") for x in existing}

    current = _load(CANDIDATES, [])
    by_id = {x.get("id"): x for x in current if x.get("id")}

    for query in DISCOVERY_QUERIES:
        try:
            results = _search(query, max_results=10)
        except Exception:
            continue

        for row in results:
            text = " ".join([row.get("title", ""), row.get("snippet", "")])
            lowered = text.lower()

            # Conservative heuristic: only consider results clearly about creators/style accounts.
            if not any(k in lowered for k in [
                "穿搭", "男装", "menswear", "fashion", "style", "outfit",
                "youtube", "bilibili", "instagram", "小红书", "抖音",
            ]):
                continue

            # Use title lead segment as a candidate display name.
            raw_name = re.split(r"[-|｜:：_]", row.get("title", ""))[0].strip()
            if len(raw_name) < 2 or len(raw_name) > 40:
                continue

            cid = _candidate_key(raw_name)
            if not cid or cid in existing_ids or raw_name.lower() in existing_names:
                continue

            item = by_id.setdefault(cid, {
                "id": cid,
                "name": raw_name,
                "status": "candidate",
                "first_seen_utc": datetime.now(timezone.utc).isoformat(),
                "last_seen_utc": None,
                "evidence_count": 0,
                "evidence": [],
                "consistency_score": 0.0,
                "personal_relevance_score": 0.0,
                "auto_promote": False,
            })
            item["last_seen_utc"] = datetime.now(timezone.utc).isoformat()
            item["evidence_count"] = int(item.get("evidence_count", 0)) + 1
            if len(item["evidence"]) < 12:
                item["evidence"].append({
                    "query": query,
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "snippet": row.get("snippet", "")[:240],
                })

            # Simple initial scores; weekly review can raise/lower these as evidence accumulates.
            ev = item["evidence_count"]
            item["consistency_score"] = round(min(1.0, 0.35 + ev * 0.04), 2)
            relevance_hits = sum(
                1 for k in ["比例", "版型", "胶囊", "基础款", "proportion", "fit", "capsule", "wardrobe"]
                if k in lowered
            )
            item["personal_relevance_score"] = round(min(1.0, 0.45 + relevance_hits * 0.08), 2)
            item["auto_promote"] = (
                item["evidence_count"] >= 5
                and item["consistency_score"] >= 0.65
                and item["personal_relevance_score"] >= 0.70
            )

    rows = sorted(
        by_id.values(),
        key=lambda x: (
            not bool(x.get("auto_promote")),
            -float(x.get("personal_relevance_score", 0)),
            -int(x.get("evidence_count", 0)),
        ),
    )
    _save(CANDIDATES, rows)
    return rows


def promote_qualified_candidates(max_new=3):
    candidates = discover_creator_candidates()
    creators = _load(CREATORS, [])
    existing_ids = {x.get("id") for x in creators}
    added = []

    for row in candidates:
        if len(added) >= max_new:
            break
        if not row.get("auto_promote") or row.get("id") in existing_ids:
            continue

        creator = {
            "id": row["id"],
            "name": row["name"],
            "region": "unknown",
            "platforms": [],
            "role": "discovered",
            "focus": ["menswear", "fit", "proportion"],
            "fit_for_agent": ["practical"],
            "enabled": True,
            "discovered_automatically": True,
            "search_queries": [
                f'\"{row["name"]}\" menswear outfit',
                f'\"{row["name"]}\" 穿搭',
            ],
        }
        creators.append(creator)
        existing_ids.add(row["id"])
        row["status"] = "promoted"
        added.append(creator)

    _save(CREATORS, creators)
    _save(CANDIDATES, candidates)
    return added
