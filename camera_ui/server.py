from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import sys

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "camera_ui" / ".env")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vision.style_vision import analyze_frame as run_style_vision
from vision.profile_extractor import extract_visual_profile
from vision.profile_collector import append_profile_observation
from vision.profile_collector import _load as load_profile_data

app = Flask(__name__, static_folder=".")

@app.get("/")
def index():
    return send_from_directory(Path(__file__).parent, "index.html")

@app.get("/camera.js")
def camera_js():
    return send_from_directory(Path(__file__).parent, "camera.js")

@app.get("/profile")
def profile_page():
    return send_from_directory(Path(__file__).parent, "profile.html")

@app.get("/profile-data")
def profile_data():
    return jsonify(load_profile_data())

@app.post("/analyze-frame")
def analyze_frame():
    if "frame" not in request.files:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    frame = request.files["frame"]
    payload = frame.read()

    try:
        result = run_style_vision(
            payload,
            frame.mimetype or "image/jpeg",
        )
        result["received_bytes"] = len(payload)
        result["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        return jsonify(result)
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
            "received_bytes": len(payload),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }), 500

@app.post("/analyze-profile")
def analyze_profile():
    if "frame" not in request.files:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    frame = request.files["frame"]
    payload = frame.read()

    try:
        result = extract_visual_profile(
            payload,
            frame.mimetype or "image/jpeg",
        )
        if result.get("ok"):
            result["merged_profile"] = append_profile_observation(result["profile"])
        result["received_bytes"] = len(payload)
        result["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        return jsonify(result)
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
            "received_bytes": len(payload),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
