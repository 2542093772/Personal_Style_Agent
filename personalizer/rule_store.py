import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
VISUAL_PROFILE_PATH = ROOT / "personal" / "visual_profile.json"
STYLE_RULES_PATH = ROOT / "personal" / "visual_style_rules.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_rules(data: Dict[str, Any]):
    STYLE_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    STYLE_RULES_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return data
