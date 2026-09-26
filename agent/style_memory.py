import json
from pathlib import Path

class StyleMemory:
    def __init__(self, feedback_path="data/feedback.json"):
        self.path = Path(feedback_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def all(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, outfit_id, feedback, score=None):
        data = self.all()
        data.append({
            "outfit_id": outfit_id,
            "feedback": feedback,
            "score": score,
        })
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
