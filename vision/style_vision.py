import base64
import json
import os
from pathlib import Path

import yaml
from openai import OpenAI


PROFILE_PATH = Path("config/profile.yaml")
LEARNED_RULES_PATH = Path("personal/learned_rules.json")


SYSTEM_PROMPT = """You are the visual analysis module of a personal men's style agent.
Analyze only visible styling information. Do not infer sensitive traits.
Focus on clothing fit, silhouette, proportions, color coordination, layering,
shoe relationship, visible grooming/style coherence, and camera framing quality.

Return ONLY valid JSON with this shape:
{
  "frame_quality": {
    "full_body_visible": true,
    "lighting_ok": true,
    "camera_distance_ok": true,
    "issues": []
  },
  "outfit": {
    "top": "",
    "bottom": "",
    "outerwear": "",
    "shoes": "",
    "colors": []
  },
  "scores": {
    "proportion_balance": 0,
    "visual_slimming": 0,
    "age_reduction": 0,
    "color_harmony": 0,
    "overall": 0
  },
  "observations": [],
  "adjustments": [],
  "confidence": 0.0
}

Scores must be integers from 0 to 100.
Keep observations concrete and visually grounded.
If the frame is insufficient, say what camera adjustment is needed instead of guessing.
"""


def _load_profile():
    if not PROFILE_PATH.exists():
        return {}
    return yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8")) or {}


def _load_learned_rules():
    if not LEARNED_RULES_PATH.exists():
        return []
    try:
        return json.loads(LEARNED_RULES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _context_text():
    profile = _load_profile()
    learned = _load_learned_rules()
    return json.dumps(
        {
            "personal_profile": profile,
            "learned_style_rules": learned[:30],
        },
        ensure_ascii=False,
    )


def analyze_frame(image_bytes: bytes, mime_type: str = "image/jpeg"):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("STYLE_VISION_MODEL")

    if not api_key:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY is not configured",
            "mode": "local_safe_fallback",
        }

    if not model:
        return {
            "ok": False,
            "error": "STYLE_VISION_MODEL is not configured",
            "mode": "local_safe_fallback",
        }

    data_url = (
        f"data:{mime_type};base64,"
        + base64.b64encode(image_bytes).decode("ascii")
    )

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": SYSTEM_PROMPT + "\nPersonal context:\n" + _context_text(),
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url,
                        "detail": "auto",
                    },
                ],
            }
        ],
    )

    text = response.output_text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {
            "frame_quality": {},
            "outfit": {},
            "scores": {},
            "observations": [text],
            "adjustments": [],
            "confidence": 0.0,
        }

    return {
        "ok": True,
        "model": model,
        "analysis": parsed,
    }
