# app.py
import os
import glob
import threading
import shutil
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory, abort, url_for

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"
VOICE_SAMPLES = "voice_samples"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(VOICE_SAMPLES, exist_ok=True)

# import generator (keeps same API as before)
from agent import run_agent

# -------------------------
# Helpers
# -------------------------
def safe_filename(filename: str) -> str:
    """Allow only base filename (no paths)."""
    return os.path.basename(filename)

def public_file_url(filename: str) -> str:
    """Return an absolute URL path for the public download route."""
    return url_for("public", filename=filename, _external=False)

def output_file_url(filename: str) -> str:
    return url_for("download", filename=filename, _external=False)

def list_public_files(limit: int = 50):
    files = sorted(glob.glob(os.path.join(PUBLIC_DIR, "*")), key=os.path.getctime, reverse=True)
    files = files[:limit]
    out = []
    for p in files:
        stat = os.stat(p)
        out.append({
            "name": os.path.basename(p),
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "public_url": public_file_url(os.path.basename(p)),
            "output_url": output_file_url(os.path.basename(p))
        })
    return out

# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download/<path:filename>")
def download(filename):
    # Prevent path traversal
    filename = safe_filename(filename)
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404, description="File not found")
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/public/<path:filename>")
def public(filename):
    filename = safe_filename(filename)
    file_path = os.path.join(PUBLIC_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404, description="File not found")
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)

@app.route("/latest")
def latest():
    files = glob.glob(os.path.join(PUBLIC_DIR, "*"))
    if not files:
        return jsonify({"error": "No file generated yet."}), 404
    latest_file = max(files, key=os.path.getctime)
    filename = os.path.basename(latest_file)
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)

@app.route("/list")
def list_files():
    """
    Returns a JSON list of recent public files with metadata.
    Frontend can poll this endpoint to detect a newly generated file.
    """
    limit = int(request.args.get("limit", 25))
    return jsonify(list_public_files(limit=limit))

@app.route("/upload_voice", methods=["POST"])
def upload_voice():
    """
    Accepts multipart file field 'voice' (wav) and saves as voice_samples/latest_sample.wav
    """
    if 'voice' not in request.files:
        return jsonify({"error": "no file field 'voice'"}), 400
    f = request.files['voice']
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = safe_filename(f.filename)
    # validate extension
    if not filename.lower().endswith(".wav"):
        return jsonify({"error": "only .wav files are supported for voice samples"}), 400

    dest = os.path.join(VOICE_SAMPLES, "latest_sample.wav")
    try:
        f.save(dest)
    except Exception as e:
        return jsonify({"error": f"failed to save: {e}"}), 500

    return jsonify({"message": "uploaded", "path": dest})

def _run_agent_thread(data: dict):
    """Wrapper to run agent in a safe thread with logging and error capture."""
    try:
        print(f"[agent thread] starting generation at {datetime.utcnow().isoformat()} for title={data.get('title')}")
        run_agent(data)
        print(f"[agent thread] finished generation at {datetime.utcnow().isoformat()}")
    except Exception as e:
        # Log the exception to console (and you can extend to writing a file)
        print("[agent thread] ERROR during run_agent:", repr(e))

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    # Start background thread (daemon so it won't block server exit)
    t = threading.Thread(target=_run_agent_thread, args=(data,), daemon=True)
    t.start()

    # Provide endpoints the frontend can use to find the result
    return jsonify({
        "message": "Generating real music/video in background (may take minutes).",
        "status": "working",
        "poll_latest": "/latest",
        "list_files": "/list"
    }), 202

# -------------------------
# Simple health / debug endpoints
# -------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

if __name__ == "__main__":
    # Production: replace with gunicorn/wsgi; for local testing this is fine
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
