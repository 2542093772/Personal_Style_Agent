import json
from pathlib import Path

CANDIDATES = Path("knowledge/candidate_rules.json")
FEEDBACK = Path("data/feedback.json")
LEARNED = Path("personal/learned_rules.json")


POSITIVE = ["好看", "显高", "显瘦", "精神", "利落", "舒服", "适合"]
NEGATIVE = ["显胖", "显老", "难看", "臃肿", "不舒服", "不适合"]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def update_personal_rules():
    candidates = _load(CANDIDATES)
    feedback = _load(FEEDBACK)
    learned = _load(LEARNED)

    positive_hits = sum(any(k in str(x.get("feedback", "")) for k in POSITIVE) for x in feedback)
    negative_hits = sum(any(k in str(x.get("feedback", "")) for k in NEGATIVE) for x in feedback)

    feedback_bias = 0.0
    total = positive_hits + negative_hits
    if total:
        feedback_bias = (positive_hits - negative_hits) / total * 0.10

    indexed = {x.get("rule_type"): x for x in learned if x.get("rule_type")}

    for c in candidates:
        score = (
            0.45 * c.get("source_reliability", 0)
            + 0.35 * c.get("personal_relevance", 0)
            + 0.20 * min(c.get("evidence_count", 0) / 5, 1.0)
            + feedback_bias
        )
        c["personal_score"] = round(max(0.0, min(score, 1.0)), 3)

        if c["personal_score"] >= 0.75:
            indexed[c["rule_type"]] = {
                **c,
                "status": "adopted",
            }

    final = list(indexed.values())
    LEARNED.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return final
