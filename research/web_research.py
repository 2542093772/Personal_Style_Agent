import json
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ddgs import DDGS

SOURCES = Path("research/sources.yaml")
TRENDS = Path("knowledge/current_trends.json")


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


def collect_daily_signals():
    cfg = load_config()
    queries = cfg.get("queries", [])
    collected = []

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
