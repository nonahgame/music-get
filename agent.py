# agent.py (REPLACE generation block with this file's content or merge carefully)
import os, random, string, shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

# import generators (guarded)
from musicgen_generator import MusicGenGenerator
from bark_generator import BarkGenerator
from mixer import mix_vocals_and_beat, create_simple_mp4
try:
    from rvc_converter import convert_with_rvc
    RVC_AVAILABLE = True
except Exception:
    RVC_AVAILABLE = False

# your existing upload_to_github function or import from tools
try:
    from agent_upload import upload_to_github  # if you extracted upload
except Exception:
    # fallback: define a simple one here (or import from your previous agent)
    import base64, requests
    GITHUB_USER = os.getenv("GITHUB_USER")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    def upload_to_github(local_file_path, github_folder="d-output"):
        try:
            filename = os.path.basename(local_file_path)
            with open(local_file_path, "rb") as f:
                content = f.read()
            encoded = base64.b64encode(content).decode("utf-8")
            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_folder}/{filename}"
            data = {"message": f"Add generated file {filename}", "content": encoded}
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            r = requests.put(url, json=data, headers=headers)
            return r.status_code in (200,201)
        except Exception as e:
            print("upload_to_github error:", e)
            return False

# instantiate generators (guard failures)
try:
    mg = MusicGenGenerator()
except Exception as e:
    print("MusicGen init failed:", e)
    mg = None
try:
    bg = BarkGenerator()
except Exception as e:
    print("Bark init failed:", e)
    bg = None

def chunker(text, max_chars=400):
    words = text.split()
    chunks, cur, cur_len = [], [], 0
    for w in words:
        if cur_len + len(w) + 1 > max_chars:
            chunks.append(" ".join(cur))
            cur = [w]; cur_len = len(w)+1
        else:
            cur.append(w); cur_len += len(w)+1
    if cur: chunks.append(" ".join(cur))
    return chunks

def run_agent(data):
    title = data.get("title","My Hit Song")
    lyrics = data.get("lyrics","Yeah yeah")
    genre = data.get("genre","hip-hop")
    voice_type = data.get("voice_type","male")  # male,female,custom
    duration = int(data.get("duration", 30))
    use_rvc = data.get("use_rvc", True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = ''.join(random.choices(string.ascii_lowercase+string.digits, k=6))
    base = f"{''.join(c if c.isalnum() else '_' for c in title)[:25]}_{ts}_{uid}"

    # 1) generate instrumental (wav)
    beat_wav = os.path.join(OUTPUT_DIR, f"{base}_beat.wav")
    if mg:
        mg.generate(prompt=f"{genre} instrumental", duration=duration, out_path=beat_wav)
    else:
        # fallback: create silent beat
        from pydub import AudioSegment
        AudioSegment.silent(duration=duration*1000).export(beat_wav, format="wav")

    # 2) generate vocals (Bark)
    vocals_wav = os.path.join(OUTPUT_DIR, f"{base}_vocals_bark.wav")
    if bg:
        # if user requested custom and sample exists, pass that logic in bark (scaffold)
        if voice_type == "custom":
            # user uploaded sample should be at voice_samples/latest_sample.wav
            sample = os.path.join("voice_samples","latest_sample.wav")
            if os.path.exists(sample):
                print("[agent] custom voice sample found; Bark generator may use it if supported.")
            else:
                print("[agent] custom requested but no sample found; defaulting to male.")
                voice_type = "male"
        bg.generate_vocals(lyrics=lyrics, voice=voice_type, out_wav=vocals_wav)
    else:
        # fallback silent vocals
        from pydub import AudioSegment
        AudioSegment.silent(duration=duration*1000).export(vocals_wav, format="wav")

    # 2.5) optional RVC conversion
    final_vocals = vocals_wav
    if voice_type == "custom" and use_rvc and RVC_AVAILABLE:
        rvc_model_path = os.getenv("RVC_MODEL_PATH")  # set this in .env to point to your RVC model
        final_vocals_rvc = os.path.join(OUTPUT_DIR, f"{base}_vocals_rvc.wav")
        convert_with_rvc(vocals_wav, final_vocals_rvc, rvc_model_path)
        final_vocals = final_vocals_rvc

    # 3) mix vocals + beat -> mp3
    final_mp3 = os.path.join(OUTPUT_DIR, f"{base}_FINAL.mp3")
    mix_vocals_and_beat(beat_wav, final_vocals, final_mp3, vocals_gain_dB=0.0)

    # 4) create MP4(s)
    lyrics_txt = os.path.join(OUTPUT_DIR, f"{base}_lyrics.txt")
    with open(lyrics_txt, "w", encoding="utf-8") as f:
        f.write(lyrics)

    final_mp4_simple = os.path.join(OUTPUT_DIR, f"{base}_FINAL_simple.mp4")
    create_simple_mp4(final_mp3, final_mp4_simple, title=title, lyrics_file=lyrics_txt)

    # Optional: create high_mp4 (if you have stock/video asset) - placeholder, reuse simple
    final_mp4_high = os.path.join(OUTPUT_DIR, f"{base}_FINAL_high.mp4")
    shutil.copy(final_mp4_simple, final_mp4_high)

    # 5) copy to public_downloads
    try:
        shutil.copy(final_mp3, os.path.join(PUBLIC_DIR, os.path.basename(final_mp3)))
        shutil.copy(final_mp4_simple, os.path.join(PUBLIC_DIR, os.path.basename(final_mp4_simple)))
        shutil.copy(final_mp4_high, os.path.join(PUBLIC_DIR, os.path.basename(final_mp4_high)))
    except Exception as e:
        print("copy to public failed:", e)

    # 6) upload to GitHub
    try:
        upload_to_github(final_mp3)
        upload_to_github(final_mp4_simple)
        upload_to_github(final_mp4_high)
    except Exception as e:
        print("GitHub upload failed:", e)

    print("Generation completed:", final_mp3, final_mp4_simple, final_mp4_high)