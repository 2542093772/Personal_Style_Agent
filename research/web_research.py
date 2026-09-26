import json
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ddgs import DDGS

SOURCES = Path("research/sources.yaml")
TRENDS = Path("knowledge/current_trends.json")
CREATORS = Path("research/creators.json")


def load_config():
    return yaml.safe_load(SOURCES.read_text(encoding="utf-8"))


def search_once(query, max_results=8):
    rows = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            rows.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })
    return rows


def load_creators():
    if not CREATORS.exists():
        return []
    try:
        data = json.loads(CREATORS.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def collect_creator_signals(max_creators=None):
    creators = [x for x in load_creators() if x.get("enabled", True)]
    if max_creators:
        creators = creators[:max_creators]

    collected = []
    for creator in creators:
        for query in creator.get("search_queries", [])[:3]:
            try:
                results = search_once(query, max_results=4)
            except Exception as exc:
                results = [{"error": str(exc)}]

            collected.append({
                "source_type": "creator",
                "creator_id": creator.get("id"),
                "creator_name": creator.get("name"),
                "creator_role": creator.get("role"),
                "creator_focus": creator.get("focus", []),
                "query": query,
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "results": results,
            })
    return collected


def collect_daily_signals():
    cfg = load_config()
    queries = cfg.get("queries", [])
    collected = []

    # Stable creator-learning track first, then broad trend discovery.
    collected.extend(collect_creator_signals())

    for query in queries:
        try:
            results = search_once(query, max_results=6)
        except Exception as exc:
            results = [{"error": str(exc)}]

        collected.append({
            "query": query,
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "results": results,
        })

    TRENDS.parent.mkdir(parents=True, exist_ok=True)
    TRENDS.write_text(
        json.dumps(collected, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return collected
