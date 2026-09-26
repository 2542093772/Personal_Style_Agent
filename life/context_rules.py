from typing import Any, Dict, List


def weather_summary(weather: Dict[str, Any] | None) -> str:
    if not weather:
        return "天气暂不可用"
    if not weather.get("ok", False):
        return f"{weather.get('location', '')} 天气获取失败"

    location = weather.get("location", "")
    low = weather.get("temp_min_c")
    high = weather.get("temp_max_c")
    apparent = weather.get("apparent_temperature_c")
    rain = weather.get("precipitation_probability_max")
    parts = [location]
    if low is not None and high is not None:
        parts.append(f"{low}–{high}℃")
    if apparent is not None:
        parts.append(f"体感 {apparent}℃")
    if rain is not None:
        parts.append(f"降水概率 {rain}%")
    return "｜".join(parts)


def weather_actions(weather: Dict[str, Any] | None) -> List[str]:
    if not weather or not weather.get("ok"):
        return []

    actions = []
    high = weather.get("temp_max_c")
    low = weather.get("temp_min_c")
    rain = weather.get("precipitation_probability_max")
    wind = weather.get("wind_kmh")

    if high is not None:
        if high >= 28:
            actions.append("天气偏热：优先轻薄、透气、少层次，避免厚重外套。")
        elif high <= 15:
            actions.append("天气偏凉：增加外层或针织层，保持利落而不是堆厚。")
        elif high <= 22:
            actions.append("温度适中：适合长裤 + 薄外层/长袖的轻层次组合。")

    if low is not None and high is not None and high - low >= 8:
        actions.append("昼夜温差较大：选择可脱穿的轻外层。")

    if rain is not None and rain >= 40:
        actions.append("有明显降水概率：带伞，鞋子优先耐脏/耐水，避免浅色麂皮。")

    if wind is not None and wind >= 25:
        actions.append("风较大：外层优先有一定防风性，避免过于飘软。")

    return actions
