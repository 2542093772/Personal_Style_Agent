import json
from pathlib import Path
import yaml

from agent.outfit_planner import OutfitPlanner, OutfitRequest
from agent.style_memory import StyleMemory

class PersonalStyleAgent:
    def __init__(self):
        self.profile = yaml.safe_load(Path("config/profile.yaml").read_text(encoding="utf-8"))
        self.rules = yaml.safe_load(Path("config/style_rules.yaml").read_text(encoding="utf-8"))
        self.wardrobe = json.loads(Path("data/wardrobe.json").read_text(encoding="utf-8"))
        self.memory = StyleMemory()

    def recommend(self, temperature_c, rain=False, occasion="daily"):
        planner = OutfitPlanner(self.wardrobe)
        return planner.recommend(
            OutfitRequest(
                temperature_c=temperature_c,
                rain=rain,
                occasion=occasion,
            )
        )

    def record_feedback(self, outfit_id, feedback, score=None):
        self.memory.add(outfit_id, feedback, score)
