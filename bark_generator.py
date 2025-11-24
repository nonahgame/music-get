# bark_generator.py
import os, math, uuid
from pathlib import Path

# guarded imports
try:
    from bark import generate_audio, preload_models, save_audio, SAMPLE_RATE
    BARK_AVAILABLE = True
except Exception as e:
    BARK_AVAILABLE = False
    print("[bark_generator] WARNING: bark not available:", e)

def ensure_bark():
    if not BARK_AVAILABLE:
        raise RuntimeError("Bark package not installed. Install and retry.")

class BarkGenerator:
    def __init__(self):
        if BARK_AVAILABLE:
            preload_models()
        else:
            print("[BarkGenerator] bark not installed; vocals won't generate.")

    def _chunks(self, text: str, max_chars=500):
        # split on whitespace into chunks of <= max_chars
        words = text.split()
        chunks, cur = [], []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > max_chars:
                chunks.append(" ".join(cur))
                cur = [w]
                cur_len = len(w) + 1
            else:
                cur.append(w)
                cur_len += len(w) + 1
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    def generate_vocals(self, lyrics: str, voice: str, out_wav: str):
        """
        lyrics: full text (up to ~6000 words)
        voice: 'male','female','custom'
        out_wav: output path
        """
        ensure_bark()
        # split lyrics into manageable chunks
        chunks = self._chunks(lyrics, max_chars=400)  # tune size
        print(f"[BarkGenerator] split into {len(chunks)} chunks")
        tmp_files = []
        for i, chunk in enumerate(chunks):
            # craft prompt
            style = "deep male singer" if voice == "male" else "female soulful singer" if voice == "female" else "male singer"
            prompt = f"{style}. Sing the following lyrics melodically:\n\n{chunk}"
            tmp_out = f"{out_wav}.part{i}.wav"
            print(f"[Bark] generating chunk {i+1}/{len(chunks)} -> {tmp_out}")
            audio_arr = generate_audio(prompt)  # depends on bark API; returns numpy arr or similar
            # save
            try:
                save_audio(audio_arr, tmp_out)
            except Exception:
                import soundfile as sf
                sf.write(tmp_out, audio_arr, SAMPLE_RATE)
            tmp_files.append(tmp_out)

        # concatenate chunks using ffmpeg concat
        concat_list = f"{out_wav}.files.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in tmp_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        # ffmpeg concat
        os.system(f"ffmpeg -y -f concat -safe 0 -i \"{concat_list}\" -c copy \"{out_wav}\"")
        # cleanup
        for p in tmp_files:
            try:
                os.remove(p)
            except: pass
        try:
            os.remove(concat_list)
        except: pass
        return out_wav