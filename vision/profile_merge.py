import json
from pathlib import Path
from datetime import datetime, timezone

PROFILE_PATH = Path("personal/visual_profile.json")


def load_visual_profile():
    if not PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def merge_visual_profile(observation):
    current = load_visual_profile()
    history = current.get("observations", [])

    history.append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "profile": observation,
    })
    history = history[-20:]

    merged = {
        "version": 1,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest": observation,
        "observations": history,
    }

    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return merged
