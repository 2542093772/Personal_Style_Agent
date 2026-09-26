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
from vision.local_profile_extractor import extract_local_visual_profile
from vision.profile_collector import append_profile_observation
from vision.profile_collector import _load as load_profile_data
from sync.github_profile_sync import sync_profile_async, get_sync_status

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
    data = load_profile_data()
    data["github_sync"] = get_sync_status()
    return jsonify(data)

@app.get("/sync-status")
def sync_status():
    return jsonify(get_sync_status())

@app.post("/sync-profile-now")
def sync_profile_now():
    return jsonify(sync_profile_async(force=True))

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
        result = extract_local_visual_profile(payload)
        if result.get("ok"):
            result["merged_profile"] = append_profile_observation(result["profile"])
            result["github_sync"] = sync_profile_async(force=False)
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
