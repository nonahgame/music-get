# mixer.py
import os, subprocess
from pydub import AudioSegment

def mix_vocals_and_beat(beat_path, vocals_path, out_mp3, vocals_gain_dB=0.0):
    beat = AudioSegment.from_file(beat_path)
    vocals = AudioSegment.from_file(vocals_path)

    # Loop/trim beat to vocal length
    if len(beat) < len(vocals):
        times = int(len(vocals) / len(beat)) + 1
        beat = beat * times
    beat = beat[:len(vocals)]
    vocals = vocals[:len(beat)]

    vocals = vocals + vocals_gain_dB

    mixed = beat.overlay(vocals)
    mixed.export(out_mp3, format="mp3", bitrate="192k")
    return out_mp3

def create_simple_mp4(audio_path, out_mp4, title=None, lyrics_file=None):
    # lyrics_file optional; create simple black bg video and burn title + lyrics via textfile
    title_escaped = (title or "").replace("'", "\\'")
    lyrics_arg = ""
    if lyrics_file and os.path.exists(lyrics_file):
        lyrics_arg = f",drawtext=textfile='{lyrics_file}':fontcolor=yellow:fontsize=28:x=(w-text_w)/2:y=h-th-120"
    cmd = f'''
    ffmpeg -y -i "{audio_path}" -f lavfi -i color=c=black:s=1280x720:d=300 \
    -filter_complex "[1:v]drawtext=text='{title_escaped}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=100:box=1:boxcolor=black@0.8{lyrics_arg}" \
    -c:v libx264 -c:a aac -b:a 192k -shortest "{out_mp4}"
    '''
    subprocess.run(cmd, shell=True, check=True)
    return out_mp4