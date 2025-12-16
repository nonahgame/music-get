# musicgen_generator.py
import os
import torch

# Compatibility fix for PyTorch 2.1.0 pytree registration (MusicGen check fails without this)
if not hasattr(torch.utils._pytree, 'register_pytree_node'):
    torch.utils._pytree.register_pytree_node = torch.utils._pytree._register_pytree_node

try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    MUSICGEN_AVAILABLE = True
except Exception as e:
    MUSICGEN_AVAILABLE = False
    MusicGen = None
    audio_write = None
    print("[musicgen_generator] WARNING: MusicGen not installed:", e)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class MusicGenGenerator:
    def __init__(self, model_name="facebook/musicgen-small"):
        if not MUSICGEN_AVAILABLE:
            raise RuntimeError("MusicGen not available. Install audiocraft.")
        self.model = MusicGen.get_pretrained(model_name).to(DEVICE)

    def generate(self, prompt: str, duration: int, out_path: str):
        """
        prompt: style/description
        duration: seconds (e.g., 30, 60)
        out_path: output wav path
        """
        print(f"[MusicGen] prompt={prompt} duration={duration}s -> {out_path}")
        self.model.set_generation_params(duration=duration)
        wavs = self.model.generate(descriptions=[prompt])
        # write wav
        audio_write(out_path, wavs[0].cpu(), self.model.sample_rate)

        return out_path
