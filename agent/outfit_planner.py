from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class OutfitRequest:
    temperature_c: float
    rain: bool
    occasion: str

class OutfitPlanner:
    def __init__(self, wardrobe: List[Dict[str, Any]]):
        self.wardrobe = wardrobe

    def _weather_ok(self, item, req: OutfitRequest):
        tmin = item.get("temp_min", -50)
        tmax = item.get("temp_max", 60)
        if not (tmin <= req.temperature_c <= tmax):
            return False
        if req.rain and item.get("avoid_rain", False):
            return False
        return True

    def recommend(self, req: OutfitRequest):
        candidates = [x for x in self.wardrobe if self._weather_ok(x, req)]
        by_type = {}
        for item in candidates:
            by_type.setdefault(item.get("type", "other"), []).append(item)

        outfit = {}
        for key in ("top", "bottom", "shoes", "outerwear"):
            if by_type.get(key):
                outfit[key] = by_type[key][0]

        return {
            "occasion": req.occasion,
            "temperature_c": req.temperature_c,
            "rain": req.rain,
            "outfit": outfit,
            "reason": "MVP recommendation based on weather constraints and available wardrobe items."
        }
