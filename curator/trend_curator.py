import json
from pathlib import Path

TRENDS = Path("knowledge/current_trends.json")
CANDIDATES = Path("knowledge/candidate_rules.json")


KEYWORDS = {
    "proportion": ["比例", "显高", "显瘦", "腿长", "腰线", "肩线", "proportion", "silhouette"],
    "color": ["配色", "色彩", "同色系", "contrast", "color"],
    "layering": ["叠穿", "layer", "layering"],
    "smart_casual": ["通勤", "smart casual", "casual tailoring"],
}


def build_candidates():
    data = json.loads(TRENDS.read_text(encoding="utf-8")) if TRENDS.exists() else []
    buckets = {}

    for batch in data:
        for result in batch.get("results", []):
            text = " ".join([
                result.get("title", ""),
                result.get("snippet", ""),
            ]).lower()

            for rule_type, kws in KEYWORDS.items():
                if any(k.lower() in text for k in kws):
                    item = buckets.setdefault(rule_type, {
                        "rule_type": rule_type,
                        "evidence_count": 0,
                        "evidence": [],
                        "source_reliability": 0.70,
                        "personal_relevance": 0.50,
                    })
                    item["evidence_count"] += 1
                    if batch.get("source_type") == "creator":
                        item["source_reliability"] = max(item["source_reliability"], 0.82)
                        item["personal_relevance"] = max(item["personal_relevance"], 0.72)
                    if len(item["evidence"]) < 12:
                        item["evidence"].append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "source_type": batch.get("source_type", "generic"),
                            "creator_id": batch.get("creator_id"),
                            "creator_name": batch.get("creator_name"),
                        })

    candidates = list(buckets.values())
    CANDIDATES.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return candidates
