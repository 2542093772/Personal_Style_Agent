import base64
import json
import os
from openai import OpenAI

PROFILE_PROMPT = """You are the visual profiling module of a personal men's style agent.
Your task is to extract only styling-relevant visible characteristics from the image.

Do NOT infer race, ethnicity, religion, health status, sexual orientation, identity, personality, socioeconomic status, or other sensitive traits.
Do NOT make attractiveness judgments.

Return ONLY valid JSON with this shape:
{
  "frame_quality": {
    "full_body_visible": false,
    "face_visible": false,
    "feet_visible": false,
    "lighting_ok": false,
    "camera_angle_ok": false,
    "issues": []
  },
  "face_and_head": {
    "face_shape": "",
    "face_length_impression": "",
    "jawline_impression": "",
    "forehead_visibility": "",
    "head_shape_notes": [],
    "confidence": 0.0
  },
  "hair": {
    "length": "",
    "volume": "",
    "texture_impression": "",
    "current_shape": "",
    "styling_notes": [],
    "confidence": 0.0
  },
  "body_proportions": {
    "shoulder_width_impression": "",
    "shoulder_to_waist_relation": "",
    "torso_length_impression": "",
    "leg_length_impression": "",
    "head_to_body_ratio_impression": "",
    "overall_build_impression": "",
    "posture_notes": [],
    "confidence": 0.0
  },
  "clothing_fit_baseline": {
    "top_fit": "",
    "bottom_fit": "",
    "waist_position_impression": "",
    "hem_length_notes": [],
    "silhouette_notes": []
  },
  "style_relevant_summary": [],
  "recommended_next_views": []
}

Use cautious language such as 'appears', 'visually reads as', or 'cannot determine from this frame' where appropriate.
If the frame is insufficient, leave uncertain fields empty and request a better view.
"""


def extract_visual_profile(image_bytes: bytes, mime_type: str = "image/jpeg"):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("STYLE_VISION_MODEL")

    if not api_key or not model:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY or STYLE_VISION_MODEL is not configured",
            "mode": "local_safe_fallback",
        }

    data_url = (
        f"data:{mime_type};base64,"
        + base64.b64encode(image_bytes).decode("ascii")
    )

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": PROFILE_PROMPT},
                {"type": "input_image", "image_url": data_url, "detail": "high"},
            ],
        }],
    )

    raw = response.output_text.strip()
    try:
        profile = json.loads(raw)
    except json.JSONDecodeError:
        profile = {
            "frame_quality": {},
            "style_relevant_summary": [raw],
            "recommended_next_views": [],
        }

    return {
        "ok": True,
        "model": model,
        "profile": profile,
    }
