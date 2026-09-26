import json
from pathlib import Path

REGISTRY = Path("research/creators.json")

def load_creators():
    if not REGISTRY.exists():
        return []
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def upsert_creator(creator):
    creators = load_creators()
    key = (creator.get("platform"), creator.get("handle"))
    replaced = False
    for i, item in enumerate(creators):
        if (item.get("platform"), item.get("handle")) == key:
            creators[i] = {**item, **creator}
            replaced = True
            break
    if not replaced:
        creators.append(creator)
    REGISTRY.write_text(json.dumps(creators, ensure_ascii=False, indent=2), encoding="utf-8")
    return creator
