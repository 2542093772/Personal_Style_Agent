import json
from pathlib import Path
from uuid import uuid4

WARDROBE_PATH = Path("data/wardrobe.json")

def load_wardrobe():
    if not WARDROBE_PATH.exists():
        return []
    return json.loads(WARDROBE_PATH.read_text(encoding="utf-8"))

def add_item(name, item_type, color="", temp_min=-50, temp_max=60, avoid_rain=False):
    items = load_wardrobe()
    item = {
        "id": str(uuid4()),
        "name": name,
        "type": item_type,
        "color": color,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "avoid_rain": avoid_rain,
    }
    items.append(item)
    WARDROBE_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return item
