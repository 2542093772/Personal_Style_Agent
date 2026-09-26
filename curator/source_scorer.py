def creator_score(metrics):
    score = 0.50
    score += 0.20 * metrics.get("explains_proportion_logic", 0)
    score += 0.15 * metrics.get("repeatable_outfit_formulas", 0)
    score += 0.15 * metrics.get("seasonal_practicality", 0)
    score += 0.10 * metrics.get("multiple_body_types", 0)

    score -= 0.20 * metrics.get("excessive_ads", 0)
    score -= 0.15 * metrics.get("trend_chasing_without_explanation", 0)
    score -= 0.20 * metrics.get("inconsistent_style_logic", 0)
    score -= 0.20 * metrics.get("body_type_mismatch", 0)

    return max(0.0, min(1.0, score))
