def compare_outfits(previous, current):
    if not previous:
        return {
            "has_previous": False,
            "changes": [],
            "score_delta": {},
            "verdict": "first_frame",
        }

    changes = []
    prev_outfit = previous.get("outfit", {})
    curr_outfit = current.get("outfit", {})

    for key in ("top", "bottom", "outerwear", "shoes"):
        if prev_outfit.get(key) != curr_outfit.get(key):
            changes.append({
                "item": key,
                "before": prev_outfit.get(key, ""),
                "after": curr_outfit.get(key, ""),
            })

    deltas = {}
    prev_scores = previous.get("scores", {})
    curr_scores = current.get("scores", {})
    for key in ("proportion_balance", "visual_slimming", "age_reduction", "color_harmony", "overall"):
        if key in prev_scores and key in curr_scores:
            deltas[key] = curr_scores[key] - prev_scores[key]

    overall = deltas.get("overall", 0)
    if overall >= 5:
        verdict = "better"
    elif overall <= -5:
        verdict = "worse"
    else:
        verdict = "similar"

    return {
        "has_previous": True,
        "changes": changes,
        "score_delta": deltas,
        "verdict": verdict,
    }
