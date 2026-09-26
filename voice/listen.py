"""Voice commands with bounded endpoint detection and caller-owned text fallback."""
from voice.stt import transcribe
import numpy as np
from audio_intelligence.recorder import (
    record_until_silence, MicrophoneUnavailableError, NoSpeechError, AudioQualityError,
)


def listen(*, device=None, sample_rate=16000, start_timeout=5.0,
           max_duration=15.0, silence_duration=0.8, backend=None, google_fallback=None):
    """Return a recognized command, or empty text so main prompts for typed input.

    Audio remains in memory. Backend selection and Google fallback are configurable.
    KeyboardInterrupt is deliberately left to the terminal loop.
    """
    try:
        audio_data = record_until_silence(
            sample_rate, device=device, start_timeout=start_timeout,
            max_duration=max_duration, silence_duration=silence_duration,
        )
        samples = np.asarray(audio_data)
        if (samples.size == 0 or samples.dtype != np.int16
                or samples.ndim != 2 or samples.shape[1] != 1):
            raise NoSpeechError("The microphone returned empty or invalid audio.")
        rms = float(np.sqrt(np.mean((samples.astype(np.float64) / 32768) ** 2)))
        if rms < 1e-5:
            raise NoSpeechError("The microphone captured silence.")
        print("Recognizing...")
        return transcribe(samples, sample_rate, backend=backend, google_fallback=google_fallback)
    except (MicrophoneUnavailableError, NoSpeechError, AudioQualityError) as error:
        print(error)
    except Exception as error:
        print("Voice input failed; switching to text:", error)
    return ""
