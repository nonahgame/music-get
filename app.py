# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import threading, os, glob
from dotenv import load_dotenv
load_dotenv()

#from flask import request
import pathlib

app = Flask(__name__)
OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)
# ensure voice_samples folder
os.makedirs("voice_samples", exist_ok=True)

from agent import run_agent

@app.route("/")
def index():
    return render_template("index.html")

# Download directly from server output folder
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

# Public accessible folder
@app.route("/public/<filename>")
def public(filename):
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)

# NEW → always return the latest generated file
@app.route("/latest")
def latest():
    files = glob.glob(os.path.join(PUBLIC_DIR, "*"))
    if not files:
        return "No file generated yet.", 404
    latest_file = max(files, key=os.path.getctime)
    filename = os.path.basename(latest_file)
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)

# ensure voice_samples folder
#os.makedirs("voice_samples", exist_ok=True)

@app.route("/upload_voice", methods=["POST"])
def upload_voice():
    """
    Accepts multipart file field 'voice' (wav) and saves as voice_samples/latest_sample.wav
    """
    if 'voice' not in request.files:
        return jsonify({"error":"no file"}), 400
    f = request.files['voice']
    filename = "latest_sample.wav"
    dest = os.path.join("voice_samples", filename)
    f.save(dest)
    return jsonify({"message":"uploaded", "path": dest})

# Trigger AI generation
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    # Run agent in background
    threading.Thread(target=run_agent, args=(data,)).start()

    return jsonify({
        "message": "Generating real music video... (2–6 minutes)",
        "status": "working"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)