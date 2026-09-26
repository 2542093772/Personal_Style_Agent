from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from datetime import datetime, timezone

app = Flask(__name__, static_folder=".")

@app.get("/")
def index():
    return send_from_directory(Path(__file__).parent, "index.html")

@app.get("/camera.js")
def camera_js():
    return send_from_directory(Path(__file__).parent, "camera.js")

@app.post("/analyze-frame")
def analyze_frame():
    if "frame" not in request.files:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    frame = request.files["frame"]
    payload = frame.read()

    # Placeholder analysis endpoint.
    # Next step: connect this endpoint to the vision/style analysis pipeline.
    return jsonify({
        "ok": True,
        "received_bytes": len(payload),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": {
            "status": "vision_backend_not_connected_yet",
            "message": "Frame received. Visual outfit analysis backend will be connected in the next iteration."
        }
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
