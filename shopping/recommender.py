def score_product(product, context):
    weights = context.get("weights", {
        "personal_fit": 0.35,
        "style_fit": 0.20,
        "wardrobe_gap": 0.15,
        "quality_value": 0.15,
        "seller_reliability": 0.10,
        "trend_relevance": 0.05,
    })

    score = (
        weights["personal_fit"] * product.get("personal_fit_score", 0.0)
        + weights["style_fit"] * product.get("style_fit_score", 0.0)
        + weights["wardrobe_gap"] * product.get("wardrobe_gap_score", 0.0)
        + weights["quality_value"] * product.get("quality_value_score", 0.0)
        + weights["seller_reliability"] * product.get("seller_reliability", 0.0)
        + weights["trend_relevance"] * product.get("trend_relevance_score", 0.0)
    )
    return round(max(0.0, min(score, 1.0)), 3)


def explain_product(product):
    reasons = []
    if product.get("personal_fit_score", 0) >= 0.75:
        reasons.append("版型与个人特征匹配")
    if product.get("wardrobe_gap_score", 0) >= 0.75:
        reasons.append("能补足现有衣柜缺口")
    if product.get("seller_reliability", 0) >= 0.85:
        reasons.append("销售渠道可靠")
    if product.get("quality_value_score", 0) >= 0.75:
        reasons.append("价格与质量平衡较好")
    return "；".join(reasons) if reasons else "需要更多个人档案和商品信息后判断"
