def similarity_score(personal, celebrity):
    score = 0.0
    weights = {
        "build": 0.20,
        "shoulder_width": 0.15,
        "torso_leg_ratio": 0.20,
        "face_shape": 0.15,
        "hair_volume": 0.10,
        "visual_age": 0.10,
        "style_goal_overlap": 0.10,
    }

    for key, weight in weights.items():
        if personal.get(key) and celebrity.get(key) and personal.get(key) == celebrity.get(key):
            score += weight

    return round(min(score, 1.0), 3)


def transferable_rules(celebrity_profile, personal_profile):
    rules = []
    for formula in celebrity_profile.get("style", {}).get("signature_formulas", []):
        if formula.get("transferable", True):
            rules.append(formula)
    return rules
