"""Offline pyttsx3 output with optional settings and unconditional text output.

Engine creation is lazy and per response. A lock serializes calls; synthesis
remains synchronous on the caller's thread (important for native voice drivers).
"""
from dataclasses import dataclass
import math
import os
import re
from threading import RLock

_lock = RLock()


@dataclass(frozen=True)
class SpeechSettings:
    rate: int = 165
    volume: float = 1.0
    voice: str | None = None
    enabled: bool = True
    chunk_length: int = 180

    def __post_init__(self):
        if isinstance(self.rate, bool) or not isinstance(self.rate, int) or not 50 <= self.rate <= 400:
            raise ValueError("speech rate must be an integer from 50 to 400 words/minute")
        if isinstance(self.volume, bool) or not isinstance(self.volume, (int, float)) or not math.isfinite(self.volume) or not 0 <= self.volume <= 1:
            raise ValueError("speech volume must be between 0 and 1")
        if self.voice is not None and not isinstance(self.voice, str):
            raise ValueError("voice must be an installed voice ID or name")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean")
        if isinstance(self.chunk_length, bool) or not isinstance(self.chunk_length, int) or not 40 <= self.chunk_length <= 1000:
            raise ValueError("chunk_length must be an integer from 40 to 1000")

    @classmethod
    def from_environment(cls):
        enabled = os.environ.get("ASSISTANT_TTS_ENABLED", "true").strip().lower()
        if enabled not in {"true", "false", "1", "0", "yes", "no"}:
            raise ValueError("ASSISTANT_TTS_ENABLED must be true or false")
        return cls(rate=int(os.environ.get("ASSISTANT_TTS_RATE", "165")),
                   volume=float(os.environ.get("ASSISTANT_TTS_VOLUME", "1.0")),
                   voice=os.environ.get("ASSISTANT_TTS_VOICE", "").strip() or None,
                   enabled=enabled in {"true", "1", "yes"},
                   chunk_length=int(os.environ.get("ASSISTANT_TTS_CHUNK_LENGTH", "180")))


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def split_text(text, max_length=180):
    """Sentence/word-aware bounded chunks, including overlong unbroken tokens.

    No non-whitespace characters are dropped. Each chunk is nonempty and at most
    max_length characters. Whitespace is normalized before splitting.
    """
    if isinstance(max_length, bool) or not isinstance(max_length, int) or max_length < 1:
        raise ValueError("max_length must be a positive integer")
    text = clean_text(text)
    chunks = []
    while len(text) > max_length:
        prefix = text[:max_length + 1]
        boundaries = list(re.finditer(r"[.!?;:]\s", prefix))
        cut = boundaries[-1].start() + 1 if boundaries else prefix.rfind(" ")
        if cut <= 0:
            cut = max_length
        chunks.append(text[:cut].strip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def _stop(engine):
    if engine is not None:
        try:
            engine.stop()
        except Exception as error:
            print("TTS cleanup error:", error)


def list_voices():
    """Return available voice IDs/names/languages, or [] if TTS is unavailable."""
    with _lock:
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return [{"id": voice.id, "name": getattr(voice, "name", ""),
                     "languages": [str(language) for language in (getattr(voice, "languages", []) or [])]}
                    for voice in (engine.getProperty("voices") or [])]
        except Exception as error:
            print("Could not list offline voices:", error)
            return []
        finally:
            _stop(engine)


def _select_voice(engine, requested):
    if not requested:
        return
    try:
        voices = engine.getProperty("voices") or []
        exact = [voice for voice in voices if voice.id == requested]
        matches = exact or [voice for voice in voices
                            if (getattr(voice, "name", "") or "").casefold() == requested.casefold()]
        if len(matches) == 1:
            engine.setProperty("voice", matches[0].id)
        else:
            print("Requested voice is unavailable or ambiguous; using the system default.")
    except Exception as error:
        print("Could not select the requested voice; using the system default:", error)


def speak(text, *, settings=None):
    """Print the complete response once, then attempt offline speech.

    Return True if speech completed without a reported failure, False for text-only
    output or failure. This cannot guarantee that the audio was physically audible.
    Ctrl+C propagates after engine cleanup; no failed chunks are replayed.
    """
    text = clean_text(text)
    if not text:
        return False
    with _lock:
        print("Assistant:", text)
        engine = None
        tokens = []
        try:
            config = settings if settings is not None else SpeechSettings.from_environment()
            if not isinstance(config, SpeechSettings):
                raise ValueError("settings must be SpeechSettings")
            if not config.enabled or config.volume == 0:
                return False
            import pyttsx3
            engine = pyttsx3.init()
            failures = []

            def on_error(name, exception):
                failures.append(str(exception))

            def on_finish(name, completed):
                if not completed:
                    failures.append("Speech playback was interrupted")

            tokens.append(engine.connect("error", on_error))
            tokens.append(engine.connect("finished-utterance", on_finish))
            engine.setProperty("rate", config.rate)
            engine.setProperty("volume", config.volume)
            _select_voice(engine, config.voice)
            for index, chunk in enumerate(split_text(text, config.chunk_length)):
                engine.say(chunk, name=f"response-{index}")
                engine.runAndWait()
                if failures:
                    raise RuntimeError(failures[0])
            return True
        except Exception as error:
            print("Speech unavailable; full response is shown above:", error)
            return False
        finally:
            if engine is not None:
                for token in tokens:
                    try:
                        engine.disconnect(token)
                    except Exception:
                        pass
            _stop(engine)
