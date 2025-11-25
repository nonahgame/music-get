# agent.py (UPDATED FOR OPENVOICE)
import os, random, string, shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Folders
OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

# Music + Mixing
from musicgen_generator import MusicGenGenerator
from mixer import mix_vocals_and_beat

# Tools
from tools import (
    search_online_asset,
    generate_visual_mp4,
    store_generation,
    generate_voice_openvoice
)

# Optional RVC
try:
    from rvc_converter import convert_with_rvc
    RVC_AVAILABLE = True
except:
    RVC_AVAILABLE = False

# GitHub uploader fallback
try:
    from agent_upload import upload_to_github
except:
    import base64, requests
    GITHUB_USER = os.getenv("GITHUB_USER")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    def upload_to_github(local_path, github_folder="d-output"):
        try:
            filename = os.path.basename(local_path)
            with open(local_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_folder}/{filename}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            data = {"message": f"Add {filename}", "content": content}

            r = requests.put(url, json=data, headers=headers)
            return r.status_code in (200, 201)
        except Exception as e:
            print("GH upload error:", e)
            return False


# Helper: Large lyric support (6k words)
def split_lyrics(text, max_length=4000):
    chunks = []
    words = text.split()
    buff, length = [], 0
    for w in words:
        w_len = len(w) + 1
        if length + w_len > max_length:
            chunks.append(" ".join(buff))
            buff, length = [w], w_len
        else:
            buff.append(w)
            length += w_len
    if buff:
        chunks.append(" ".join(buff))
    return chunks



# ============================================================
#                MAIN AGENT LOGIC (OPENVOICE)
# ============================================================
def run_agent(data):
    title = data.get("title", "My Hit Song")
    lyrics = data.get("lyrics", "")
    genre = data.get("genre", "hip-hop")
    voice_type = data.get("voice_type", "default")   # "default", "clone"
    voice_sample = data.get("voice_sample")           # optional uploaded .wav
    file_format = data.get("file_format", "mp3")

    # Generate unique ID
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    base = f"{title.replace(' ', '_')[:25]}_{uid}"

    print("\n====================")
    print("[AGENT] STARTING JOB")
    print("====================\n")

    # ---------------------------------------------------------
    # 1. Search for image + video background
    # ---------------------------------------------------------
    print("[1] Searching background assets...")
    pic_url = search_online_asset("image", title)
    vid_url = search_online_asset("video", title)

    # ---------------------------------------------------------
    # 2. Generate instrumental using MUSICGEN
    # ---------------------------------------------------------
    print("[2] Generating instrumental...")
    instrumental = os.path.join(OUTPUT_DIR, f"{base}_instrumental.wav")

    mg = MusicGenGenerator()
    mg.generate(
        prompt=f"{genre} instrumental",
        duration=45,
        out_path=instrumental
    )

    # ---------------------------------------------------------
    # 3. Generate vocals using OPENVOICE
    # ---------------------------------------------------------
    print("[3] Generating vocals with OpenVoice...")

    vocal_raw = os.path.join(OUTPUT_DIR, f"{base}_vocals_raw.wav")

    if voice_type == "clone" and voice_sample:
        print("[OpenVoice] Using user's uploaded voice sample...")
        voice_clone_input = voice_sample
    else:
        voice_clone_input = None   # default OpenVoice voice

    generated_vocals_path = generate_voice_openvoice(
        lyrics=lyrics,
        user_id=uid,
        voice_clone_sample=voice_clone_input
    )

    final_vocals = generated_vocals_path

    # ---------------------------------------------------------
    # 4. Optional RVC voice conversion
    # ---------------------------------------------------------
    if voice_type == "clone" and RVC_AVAILABLE:
        print("[4] Applying RVC model...")
        rvc_out = os.path.join(OUTPUT_DIR, f"{base}_rvc.wav")
        model_path = os.getenv("RVC_MODEL_PATH")
        convert_with_rvc(final_vocals, rvc_out, model_path)
        final_vocals = rvc_out
    else:
        print("[4] Skipping RVC...")

    # ---------------------------------------------------------
    # 5. Mix vocals + instrumental → MP3
    # ---------------------------------------------------------
    print("[5] Mixing vocals + instrumental...")
    final_mp3 = os.path.join(OUTPUT_DIR, f"{base}.mp3")

    mix_vocals_and_beat(
        instrumental,
        final_vocals,
        final_mp3,
        vocals_gain_dB=8.0
    )

    # ---------------------------------------------------------
    # 6. Generate MP4 videos (simple + high quality)
    # ---------------------------------------------------------
    print("[6] Generating MP4 videos...")

    simple_mp4 = generate_visual_mp4(
        audio_path=final_mp3,
        file_format="simple_mp4",
        pic=pic_url,
        video=None,
        title=title,
        lyrics=lyrics.split("\n"),
        user_id=uid
    )

    high_mp4 = generate_visual_mp4(
        audio_path=final_mp3,
        file_format="high_mp4",
        pic=None,
        video=vid_url,
        title=title,
        lyrics=lyrics.split("\n"),
        user_id=uid
    )

    # ---------------------------------------------------------
    # 7. Copy to public_downloads/
    # ---------------------------------------------------------
    print("[7] Copying files to public_downloads...")
    for f in [final_mp3, simple_mp4, high_mp4]:
        try:
            shutil.copy(f, os.path.join(PUBLIC_DIR, os.path.basename(f)))
        except Exception as e:
            print("Copy error:", e)

    # ---------------------------------------------------------
    # 8. Upload to GitHub
    # ---------------------------------------------------------
    print("[8] Uploading to GitHub...")
    upload_to_github(final_mp3)
    upload_to_github(simple_mp4)
    upload_to_github(high_mp4)

    # ---------------------------------------------------------
    # 9. Store metadata log
    # ---------------------------------------------------------
    print("[9] Logging generation metadata...")
    store_generation(
        user_id=uid,
        title=title,
        lyrics=lyrics,
        file_path=final_mp3,
        file_format=file_format,
        pic_url=pic_url,
        video_url=vid_url
    )

    print("\n====================")
    print("[AGENT] DONE")
    print("====================\n")

    return {
        "audio": final_mp3,
        "simple_mp4": simple_mp4,
        "high_mp4": high_mp4,
        "uid": uid
    }
