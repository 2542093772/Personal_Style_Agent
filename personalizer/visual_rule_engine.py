from typing import Dict, Any, List


def _rule(rule_id: str, title: str, rationale: str, applies_to: List[str], confidence: float, priority: int = 50):
    return {
        "id": rule_id,
        "title": title,
        "rationale": rationale,
        "applies_to": applies_to,
        "confidence": round(float(confidence), 2),
        "priority": priority,
        "source": "visual_profile",
    }


def build_rules_from_visual_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    stable = profile.get("stable_profile", {})
    latest = profile.get("latest", {})
    body = latest.get("body_proportions", {}) if isinstance(latest, dict) else {}

    shoulder = stable.get("shoulder_width_impression") or body.get("shoulder_width_impression", "")
    torso = stable.get("torso_length_impression") or body.get("torso_length_impression", "")
    leg = stable.get("leg_length_impression") or body.get("leg_length_impression", "")
    build = stable.get("overall_build_impression") or body.get("overall_build_impression", "")
    sample_count = int(stable.get("sample_count") or 0)

    base_conf = min(0.95, 0.55 + min(sample_count, 20) * 0.02)
    rules = []

    if shoulder == "偏宽":
        rules += [
            _rule(
                "visual.shoulder.avoid_extra_width",
                "上半身避免继续横向放大",
                "当前视觉档案显示肩部偏宽，过厚肩垫、夸张落肩和高蓬松层次容易让上半身更重。",
                ["top", "outerwear"],
                base_conf,
                90,
            ),
            _rule(
                "visual.shoulder.prefer_clean_vertical",
                "优先干净纵向线条",
                "直落门襟、简洁领口和不过度膨胀的肩部结构更容易维持利落比例。",
                ["top", "outerwear"],
                base_conf,
                85,
            ),
        ]
    elif shoulder == "偏窄":
        rules += [
            _rule(
                "visual.shoulder.add_structure",
                "上衣可适度增加肩部结构",
                "肩部视觉偏窄时，可通过合身肩线、轻结构外套或横向细节增加上身存在感。",
                ["top", "outerwear"],
                base_conf,
                80,
            )
        ]

    if torso == "偏长":
        rules += [
            _rule(
                "visual.torso.raise_waist",
                "优先中高腰下装",
                "躯干视觉偏长时，提高腰线通常能改善上下身比例。",
                ["bottom"],
                base_conf,
                95,
            ),
            _rule(
                "visual.torso.avoid_long_top",
                "避免上衣下摆过长",
                "过长上衣会进一步拉长躯干视觉，优先短一些或可塞衣角的上装。",
                ["top", "outerwear"],
                base_conf,
                90,
            ),
        ]
    elif torso == "偏短":
        rules += [
            _rule(
                "visual.torso.avoid_extreme_crop",
                "避免过度短款上装",
                "躯干视觉偏短时，过高腰线和极短上装可能让上身进一步压缩。",
                ["top", "bottom"],
                base_conf,
                80,
            )
        ]

    if leg == "偏短":
        rules += [
            _rule(
                "visual.leg.high_waist",
                "优先提高腰线",
                "腿部视觉偏短时，中高腰和明确腰线通常更有利于腿部比例。",
                ["bottom"],
                base_conf,
                95,
            ),
            _rule(
                "visual.leg.clean_pants",
                "裤腿保持纵向连续",
                "减少明显截断、堆叠和强烈横向分割，有利于延长腿部视觉。",
                ["bottom", "shoes"],
                base_conf,
                90,
            ),
        ]
    elif leg == "偏长":
        rules += [
            _rule(
                "visual.leg.allow_relaxed_rise",
                "裤腰位置可更灵活",
                "腿部视觉偏长时，对腰线位置容错更高，可根据整体风格选择中腰或轻松版型。",
                ["bottom"],
                base_conf,
                75,
            )
        ]

    if build:
        rules.append(
            _rule(
                "visual.build.balance",
                "优先维持整体轮廓平衡",
                f"当前整体体型视觉记录为“{build}”，推荐以合身但不过分紧绷的轮廓作为基线，再根据单品调整。",
                ["top", "bottom", "outerwear"],
                max(0.55, base_conf - 0.05),
                70,
            )
        )

    return {
        "version": 1,
        "sample_count": sample_count,
        "generated_from": "personal/visual_profile.json",
        "rules": sorted(rules, key=lambda x: (-x["priority"], -x["confidence"])),
    }
