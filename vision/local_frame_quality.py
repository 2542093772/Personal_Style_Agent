def collection_status(profile):
    q = profile.get("frame_quality", {})
    if q.get("full_body_visible") and q.get("camera_angle_ok") and q.get("lighting_ok"):
        return "good"
    if q.get("face_visible") or q.get("feet_visible"):
        return "partial"
    return "poor"
