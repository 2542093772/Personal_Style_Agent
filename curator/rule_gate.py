def should_promote(candidate, thresholds):
    source_ok = candidate.get("source_reliability", 0) >= thresholds.get("creator_reliability", 0.70)
    relevance_ok = candidate.get("personal_relevance", 0) >= thresholds.get("personal_adoption", 0.75)
    evidence_ok = candidate.get("evidence_count", 0) >= 3
    return source_ok and relevance_ok and evidence_ok
