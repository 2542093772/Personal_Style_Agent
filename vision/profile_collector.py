import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROFILE_PATH = Path("personal/visual_profile.json")


def _load():
    if not PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _mode(values):
    values = [v for v in values if v not in (None, "", [], {})]
    if not values:
        return ""
    return Counter(values).most_common(1)[0][0]


def build_stable_profile(observations):
    face_shapes = []
    hair_lengths = []
    hair_volumes = []
    shoulder_widths = []
    torso_lengths = []
    leg_lengths = []
    builds = []

    for obs in observations:
        p = obs.get("profile", {})
        face = p.get("face_and_head", {})
        hair = p.get("hair", {})
        body = p.get("body_proportions", {})

        face_shapes.append(face.get("face_shape"))
        hair_lengths.append(hair.get("length"))
        hair_volumes.append(hair.get("volume"))
        shoulder_widths.append(body.get("shoulder_width_impression"))
        torso_lengths.append(body.get("torso_length_impression"))
        leg_lengths.append(body.get("leg_length_impression"))
        builds.append(body.get("overall_build_impression"))

    return {
        "face_shape": _mode(face_shapes),
        "hair_length": _mode(hair_lengths),
        "hair_volume": _mode(hair_volumes),
        "shoulder_width_impression": _mode(shoulder_widths),
        "torso_length_impression": _mode(torso_lengths),
        "leg_length_impression": _mode(leg_lengths),
        "overall_build_impression": _mode(builds),
        "sample_count": len(observations),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def append_profile_observation(profile):
    current = _load()
    observations = current.get("observations", [])

    observations.append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    })
    observations = observations[-60:]

    current = {
        "version": 2,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stable_profile": build_stable_profile(observations),
        "latest": profile,
        "observations": observations,
        "raw_images_saved": False,
    }

    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return current
