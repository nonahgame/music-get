# tools.py (UPDATED FOR OPENVOICE)
import os
import random
import time
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, ColorClip, ImageClip
)
from pydub import AudioSegment
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper

# ==========================
# NEW: OPENVOICE IMPORTS
# ==========================
from openvoice import se_extractor
from openvoice.api import TTS

# --- initialize TTS model ---
OPENVOICE_MODEL = TTS(language="en")
# models auto-download to ~/.cache/openvoice

OUTPUT_DIR = "output"
PUBLIC_DIR = "public_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)


# ============================================================
#  SEARCH IMAGES / VIDEOS ONLINE
# ============================================================
@tool
def search_online_asset(asset_type: str, query: str) -> str:
    """
    Search online images/videos using Google Serper API.
    Returns ONE usable URL or 'none'.
    """
    try:
        search = GoogleSerperAPIWrapper()
        results = search.results(f"{query} {asset_type} free image")
        urls = []

        for r in results.get("organic", []):
            link = r.get("link", "")
            if any(x in link for x in ["pexels.com", "unsplash.com", "pixabay.com"]):
                urls.append(link)

        return random.choice(urls) if urls else "none"
    except:
        return "none"


# ============================================================
#   NEW: GENERATE VOICE USING OPENVOICE
# ============================================================
@tool
def generate_voice_openvoice(
    lyrics: str,
    user_id: str,
    voice_clone_sample: str | None
) -> str:
    """
    Generate WAV vocals using OpenVoice.
    - lyrics: full text (up to 6000+ words)
    - user_id: unique
    - voice_clone_sample: optional path to reference voice file (wav/mp3)

    Returns: path to generated WAV file.
    """

    # --------------------------
    # Extract embedding if voice clone is provided
    # --------------------------
    if voice_clone_sample and os.path.exists(voice_clone_sample):
        try:
            print("Extracting voice embedding...")
            reference_se = se_extractor.get_se(voice_clone_sample)
        except:
            reference_se = None
    else:
        reference_se = None

    # --------------------------
    # Generate vocal audio
    # --------------------------
    out_path = f"{OUTPUT_DIR}/voice_{user_id}.wav"

    print("Generating audio with OpenVoice...")
    OPENVOICE_MODEL.tts(
        text=lyrics,
        output_path=out_path,
        speaker_embedding=reference_se,   # None = default voice
        speed=1.0
    )

    return out_path


# ============================================================
#   GENERATE MP4 / MP3 / WAV VISUAL VIDEO
# ============================================================
@tool
def generate_visual_mp4(
    audio_path: str,
    file_format: str,
    pic: str | None,
    video: str | None,
    title: str,
    lyrics: list[str],
    user_id: str
) -> str:
    """
    Generates:
      - MP3/WAV (audio only)
      - simple_mp4 (black + title + lyrics)
      - high_mp4 (merged video + audio)
    """

    audio = AudioFileClip(audio_path)

    # ======================================================
    #   SIMPLE MP4 (static background + title + lyrics)
    # ======================================================
    if file_format == "simple_mp4":

        bg_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=audio.duration)

        if pic and pic != "none":
            try:
                img = ImageClip(pic).resize((1280, 720)).set_duration(audio.duration)
                bg_clip = CompositeVideoClip([img])
            except:
                pass

        title_clip = TextClip(
            txt=title,
            fontsize=60,
            color="white"
        ).set_position("center").set_duration(audio.duration)

        footer_text = "   |   ".join(lyrics[:3])
        footer_clip = TextClip(
            txt=footer_text,
            fontsize=32,
            color="yellow"
        ).set_position(("center", "bottom")).set_duration(audio.duration)

        final = CompositeVideoClip([bg_clip, title_clip, footer_clip]).set_audio(audio)

        out_path = f"{OUTPUT_DIR}/simple_{user_id}.mp4"
        final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")
        return out_path

    # ======================================================
    #   HIGH MP4 (use downloaded video)
    # ======================================================
    if file_format == "high_mp4":

        if video and video != "none":
            try:
                vid = VideoFileClip(video).subclip(0, audio.duration).resize((1280, 720))
            except:
                vid = ColorClip(size=(1280,720), color=(0,0,0), duration=audio.duration)
        else:
            vid = ColorClip(size=(1280,720), color=(0,0,0), duration=audio.duration)

        title_clip = TextClip(
            title,
            fontsize=60,
            color="white"
        ).set_position("center").set_duration(audio.duration)

        scroll_text = "\n".join(lyrics[:40])
        lyrics_clip = TextClip(
            scroll_text,
            fontsize=28,
            color="yellow",
            align="West"
        ).set_position(("center", "bottom")).set_duration(audio.duration)

        final = CompositeVideoClip([vid, title_clip, lyrics_clip]).set_audio(audio)

        out_path = f"{OUTPUT_DIR}/high_{user_id}.mp4"
        final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")
        return out_path


    # ======================================================
    #   AUDIO ONLY
    # ======================================================
    if file_format == "wav":
        out_path = f"{OUTPUT_DIR}/audio_{user_id}.wav"
        AudioSegment.from_file(audio_path).export(out_path, format="wav")
        return out_path

    return audio_path


# ============================================================
#   STORE GENERATION METADATA
# ============================================================
@tool
def store_generation(
    user_id: str,
    title: str,
    lyrics: str,
    file_path: str,
    file_format: str,
    pic_url: str | None,
    video_url: str | None
):
    """
    Store generation metadata in simple log.
    """

    with open("generation_log.txt", "a") as f:
        f.write(
            f"\nUSER: {user_id}\n"
            f"TITLE: {title}\n"
            f"FORMAT: {file_format}\n"
            f"FILE: {file_path}\n"
            f"PIC: {pic_url}\n"
            f"VIDEO: {video_url}\n"
            f"LYRICS_LEN: {len(lyrics)}\n"
            f"---------------------------\n"
        )

    return "stored"
