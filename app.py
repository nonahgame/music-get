# app.py
import os
import glob
import threading
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory, abort, url_for

# -----------------------------------
# Environment
# -----------------------------------
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# -----------------------------------
# Directories
# -----------------------------------
OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"
VOICE_SAMPLES = "voice_samples"

for folder in [OUTPUT_DIR, PUBLIC_DIR, VOICE_SAMPLES]:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Unable to create folder {folder}: {e}")

# -----------------------------------
# SAFE IMPORT — prevents Gunicorn crash
# -----------------------------------
try:
    from agent import run_agent
except Exception as e:
    print("\n[ERROR] Could not import agent.run_agent function!\n")
    run_agent = None


# -----------------------------------
# Helpers
# -----------------------------------
def safe_filename(filename: str) -> str:
    return os.path.basename(filename)


def public_file_url(filename: str) -> str:
    return url_for("public", filename=filename, _external=False)


def output_file_url(filename: str) -> str:
    return url_for("download", filename=filename, _external=False)


def list_public_files(limit: int = 50):
    try:
        files = sorted(
            glob.glob(os.path.join(PUBLIC_DIR, "*")),
            key=os.path.getctime,
            reverse=True,
        )
    except Exception as e:
        print(f"[ERROR] Could not list public files: {e}")
        return []

    files = files[:limit]

    out = []
    for p in files:
        try:
            stat = os.stat(p)
            out.append({
                "name": os.path.basename(p),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "public_url": public_file_url(os.path.basename(p)),
                "output_url": output_file_url(os.path.basename(p))
            })
        except Exception as e:
            print(f"[ERROR] Stat failed for {p}: {e}")

    return out


# -----------------------------------
# Routes
# -----------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download/<path:filename>")
def download(filename):
    filename = safe_filename(filename)
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404)
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route("/public/<path:filename>")
def public(filename):
    filename = safe_filename(filename)
    file_path = os.path.join(PUBLIC_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404)
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)


@app.route("/latest")
def latest():
    files = glob.glob(os.path.join(PUBLIC_DIR, "*"))
    if not files:
        return jsonify({"error": "No generated file yet"}), 404
    latest_file = max(files, key=os.path.getctime)
    return send_from_directory(PUBLIC_DIR, os.path.basename(latest_file), as_attachment=True)


@app.route("/list")
def list_files():
    limit = int(request.args.get("limit", 25))
    return jsonify(list_public_files(limit=limit))


@app.route("/upload_voice", methods=["POST"])
def upload_voice():
    if "voice" not in request.files:
        return jsonify({"error": "voice file missing"}), 400

    f = request.files["voice"]
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    if not f.filename.lower().endswith(".wav"):
        return jsonify({"error": "Only WAV supported"}), 400

    dest = os.path.join(VOICE_SAMPLES, "latest_sample.wav")
    try:
        f.save(dest)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "uploaded", "path": dest})


# -----------------------------------
# BACKGROUND AGENT THREAD
# -----------------------------------
def _run_agent_thread(data: dict):
    if run_agent is None:
        print("[agent thread] ERROR: run_agent() not available")
        return

    try:
        print(f"[agent thread] Starting generation at {datetime.utcnow()}")
        run_agent(data)
        print(f"[agent thread] Finished at {datetime.utcnow()}")
    except Exception as e:
        print("[agent thread] EXCEPTION:", e)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}

    # Run agent safely in background
    threading.Thread(
        target=_run_agent_thread,
        args=(data,),
        daemon=True
    ).start()

    return jsonify({
        "message": "Generation started",
        "status": "working",
        "poll_latest": "/latest",
        "list_files": "/list"
    }), 202


# -----------------------------------
# Health
# -----------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


# -----------------------------------
# LOCAL DEV ONLY
# -----------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=True)
