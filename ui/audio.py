"""Upload decoding independent of Streamlit widgets, reusable and testable."""
import tempfile
from pathlib import Path
import wave
import numpy as np
from audio_intelligence.recorder import read_wav
from audio_intelligence.preprocessing import to_mono


def decode_upload(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > 20 * 1024 * 1024:
        raise ValueError("Choose a nonempty WAV up to 20 MiB")
    # Ignore browser filenames; only a private generated path is used.
    with tempfile.TemporaryDirectory(prefix="assistant-upload-") as directory:
        path = Path(directory) / "input.wav"
        path.write_bytes(raw)
        with wave.open(str(path), "rb") as wav:
            if not 0.1 <= wav.getnframes() / wav.getframerate() <= 60:
                raise ValueError("Audio must contain 0.1 to 60 seconds")
        return read_wav(path)


def pcm_for_stt(samples):
    return np.clip(np.rint(to_mono(samples).astype(float) * 32768), -32768, 32767).astype(np.int16)[:, None]
