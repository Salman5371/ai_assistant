"""Configurable speech-to-text. Optional engines are imported only when used."""
from functools import lru_cache
import os
import numpy as np
from audio_intelligence.preprocessing import to_mono, resample, validate_rate


def _flag(name, default):
    value = os.environ.get(name, str(default)).strip().lower()
    if value not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"{name} must be true or false")
    return value in {"true", "1", "yes"}


@lru_cache(maxsize=1)
def _whisper_model(model_name, local_only):
    from faster_whisper import WhisperModel
    return WhisperModel(model_name, device="cpu", compute_type="int8",
                        cpu_threads=min(4, os.cpu_count() or 1), num_workers=1,
                        local_files_only=local_only)


def _transcribe_whisper(samples, rate):
    model_name = os.environ.get("ASSISTANT_WHISPER_MODEL", "tiny.en").strip()
    if not model_name:
        raise ValueError("ASSISTANT_WHISPER_MODEL cannot be empty")
    model = _whisper_model(model_name, _flag("ASSISTANT_WHISPER_LOCAL_ONLY", False))
    audio = resample(to_mono(samples), rate, 16000)
    language = os.environ.get("ASSISTANT_WHISPER_LANGUAGE", "en").strip()
    segments, _ = model.transcribe(
        audio, language=None if language.lower() == "auto" else language,
        beam_size=1, best_of=1, condition_on_previous_text=False, vad_filter=True,
    )
    # Inference is lazy: errors can occur while consuming segments, not just above.
    return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()


def _transcribe_google(samples, rate):
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 10
    audio = sr.AudioData(samples.astype("<i2", copy=False).tobytes(), rate, 2)
    try:
        command = recognizer.recognize_google(audio)
        return command.strip() if isinstance(command, str) else ""
    except sr.UnknownValueError:
        print("Speech was unclear or too noisy. Please type your command or try again.")
    except sr.RequestError as error:
        print("Speech service unavailable. Check your internet connection:", error)
    except TimeoutError:
        print("Speech recognition timed out. Please type your command.")
    return ""


def transcribe(samples, sample_rate=16000, *, backend=None, google_fallback=None):
    """Return text or an empty string for the existing terminal text fallback.

    Default is Google for compatibility. 'whisper' and 'auto' try local Whisper
    first, then Google unless fallback is disabled. No second recording is made.
    """
    try:
        rate = validate_rate(sample_rate)
        samples = np.asarray(samples)
        if (samples.dtype != np.int16 or samples.ndim != 2 or samples.shape[1] != 1
                or not samples.size):
            raise ValueError("STT requires nonempty mono int16 audio")
        if np.sqrt(np.mean((samples.astype(np.float64) / 32768) ** 2)) < 1e-5:
            return ""
        choice = (backend if backend is not None else os.environ.get("ASSISTANT_STT_BACKEND", "google")).strip().lower()
        if choice not in {"google", "whisper", "auto"}:
            raise ValueError("ASSISTANT_STT_BACKEND must be google, whisper, or auto")
        if choice != "google":
            fallback = _flag("ASSISTANT_STT_GOOGLE_FALLBACK", True) if google_fallback is None else google_fallback
            if not isinstance(fallback, bool):
                raise ValueError("google_fallback must be a boolean")
            try:
                print("Recognizing with local Whisper (first use may download model weights)...")
                text = _transcribe_whisper(samples, rate)
                if text:
                    return text
                print("Whisper did not recognize any words.")
            except Exception as error:
                print(f"Whisper unavailable or transcription failed ({type(error).__name__}). "
                      "Install requirements-whisper.txt and check the model cache/settings.")
            if not fallback:
                print("Google fallback is disabled. Please type your command.")
                return ""
            print("Falling back to Google speech recognition; this sends the recording to Google.")
        return _transcribe_google(samples, rate)
    except Exception as error:
        print("Speech-to-text unavailable; please type your command:", error)
        return ""
