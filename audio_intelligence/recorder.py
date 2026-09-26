"""Microphone and PCM WAV I/O. Microphone access occurs only on explicit calls."""
from contextlib import contextmanager
from pathlib import Path
import math
import tempfile
import wave
import numpy as np
from .preprocessing import as_float, validate_rate


def record_audio(duration=5.0, sample_rate=16000, channels=1, *, device=None):
    """Record signed 16-bit PCM with the same sounddevice flow as voice.listen."""
    sample_rate = validate_rate(sample_rate)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and positive")
    if isinstance(channels, bool) or not isinstance(channels, int) or channels < 1:
        raise ValueError("channels must be a positive integer")
    frames = round(duration * sample_rate)
    if frames < 1:
        raise ValueError("duration is shorter than one sample")
    import sounddevice as sd
    try:
        samples = sd.rec(frames, samplerate=sample_rate, channels=channels,
                         dtype="int16", device=device)
        sd.wait()
        return samples.copy()
    finally:
        sd.stop()


def write_wav(path, audio, sample_rate):
    """Create a 16-bit PCM WAV without overwriting an existing file.

    Out-of-range floating samples are clipped. A failed write removes only the
    newly created file. Parent directories must already exist.
    """
    sample_rate = validate_rate(sample_rate)
    data = as_float(audio)
    channels = 1 if data.ndim == 1 else data.shape[1]
    pcm = np.clip(np.rint(np.clip(data, -1, 1).astype(np.float64) * 32768),
                  -32768, 32767).astype("<i2")
    path = Path(path)
    with path.open("xb") as stream:
        try:
            with wave.open(stream, "wb") as wav:
                wav.setnchannels(channels)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(pcm.tobytes())
        except BaseException:
            stream.close()
            path.unlink(missing_ok=True)
            raise
    return path


def read_wav(path):
    """Read integer PCM WAV as float32 plus rate; reject payloads over 128 MiB."""
    with wave.open(str(path), "rb") as wav:
        channels, width, rate, frames = (wav.getnchannels(), wav.getsampwidth(),
                                         wav.getframerate(), wav.getnframes())
        if wav.getcomptype() != "NONE" or width not in (1, 2, 3, 4):
            raise ValueError("only uncompressed integer PCM WAV is supported")
        validate_rate(rate)
        if frames * channels * width > 128 * 1024 * 1024:
            raise ValueError("Decoded WAV input exceeds 128 MiB")
        raw = wav.readframes(frames)
    if len(raw) != frames * channels * width:
        raise ValueError("WAV sample data is truncated")
    if width == 3:
        values = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        values = values[:, 0] | (values[:, 1] << 8) | (values[:, 2] << 16)
        values = (values ^ 0x800000) - 0x800000
        data = (values.astype(np.float64) / 8388608).astype(np.float32)
    else:
        data = as_float(np.frombuffer(raw, dtype={1: "u1", 2: "<i2", 4: "<i4"}[width]))
    if channels > 1:
        data = data.reshape(-1, channels)
    return data, rate


def record_wav(path, duration=5.0, sample_rate=16000, channels=1, *, device=None):
    return write_wav(path, record_audio(duration, sample_rate, channels, device=device), sample_rate)


@contextmanager
def temporary_wav(audio, sample_rate, *, directory=None):
    """Yield a closed WAV path usable on Windows; delete it even on exceptions.

    Each call owns a private temporary directory. Never deletes caller-owned files.
    """
    with tempfile.TemporaryDirectory(prefix="assistant-audio-", dir=directory) as folder:
        path = write_wav(Path(folder) / "audio.wav", audio, sample_rate)
        yield path


class MicrophoneUnavailableError(RuntimeError):
    """No usable input device or unsupported recording settings."""


class NoSpeechError(RuntimeError):
    """No sufficiently long speech-like signal was captured."""


class AudioQualityError(RuntimeError):
    """Capture was clipped, overflowed, or could not reach an endpoint."""


def check_microphone(sample_rate=16000, *, device=None):
    """Check the selected/default input device and mono PCM settings.

    Opening the stream can still fail later (permissions, disconnect, device busy).
    """
    validate_rate(sample_rate)
    try:
        import sounddevice as sd
        info = sd.query_devices(device, "input")
        if info["max_input_channels"] < 1:
            raise MicrophoneUnavailableError("The selected device has no microphone input.")
        sd.check_input_settings(device=device, channels=1, dtype="int16", samplerate=sample_rate)
        return info
    except MicrophoneUnavailableError:
        raise
    except Exception as error:
        raise MicrophoneUnavailableError(
            "Microphone unavailable. Check the input device, permissions, and sample rate."
        ) from error


def record_until_silence(sample_rate=16000, *, device=None, start_timeout=5.0,
                         max_duration=15.0, silence_duration=0.8,
                         min_speech_duration=0.2, calibration_duration=0.3,
                         threshold_db=-40.0):
    """Record mono int16 until a quiet interval follows speech-like activity.

    Calibrates while the user is prompted to remain quiet, then retains a short
    pre-roll to protect word onsets. Energy-based detection is not a speech model:
    noise/music can activate it. Continuous activity is rejected at the time cap
    rather than submitting a potentially truncated command. Fixed-duration capture
    remains available via record_audio for non-command audio workflows.
    """
    from collections import deque
    sample_rate = validate_rate(sample_rate)
    for name, value in (("start_timeout", start_timeout), ("max_duration", max_duration),
                        ("silence_duration", silence_duration),
                        ("min_speech_duration", min_speech_duration),
                        ("calibration_duration", calibration_duration)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if max_duration < min_speech_duration + silence_duration:
        raise ValueError("max_duration must allow speech plus trailing silence")
    if not math.isfinite(threshold_db) or not -100 <= threshold_db <= 0:
        raise ValueError("threshold_db must be between -100 and 0")
    check_microphone(sample_rate, device=device)
    import sounddevice as sd
    frames = max(1, round(sample_rate * 0.05))
    seconds = frames / sample_rate

    def read_block(stream):
        block, overflowed = stream.read(frames)
        if overflowed:
            raise AudioQualityError("Microphone input overflowed; please try again.")
        block = np.asarray(block)
        if block.shape != (frames, 1) or block.dtype != np.int16:
            raise AudioQualityError("The microphone returned empty or invalid audio.")
        block = block.copy()
        scaled = block.astype(np.float64) / 32768
        if np.mean(np.abs(scaled) >= 0.99) > 0.1:
            raise AudioQualityError("Audio is clipped. Lower microphone gain or move farther away.")
        return block, float(np.sqrt(np.mean(scaled ** 2)))

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16",
                            blocksize=frames, device=device) as stream:
            print("Checking background noise; please stay quiet briefly...")
            levels = [read_block(stream)[1]
                      for _ in range(math.ceil(calibration_duration / seconds))]
            noise = float(np.median(levels))
            if noise > 0.08:
                raise AudioQualityError("Background noise is too loud. Try a quieter location.")
            threshold = max(10 ** (threshold_db / 20), noise * 3)
            print("Speak now. Recording stops after a pause.")
            pre_roll = deque(maxlen=max(1, math.ceil(0.2 / seconds)))
            chunks = []
            quiet_time = active_time = phrase_time = waiting_time = 0.0
            started = False
            while True:
                block, level = read_block(stream)
                active = level > threshold
                if not started:
                    pre_roll.append(block)
                    waiting_time += seconds
                    if active:
                        started = True
                        chunks.extend(pre_roll)
                        active_time = seconds
                        phrase_time = seconds
                    elif waiting_time + 1e-9 >= start_timeout:
                        raise NoSpeechError("No speech detected before the listening timeout.")
                    continue
                chunks.append(block)
                phrase_time += seconds
                active_time += seconds if active else 0
                quiet_time = 0 if active else quiet_time + seconds
                if quiet_time + 1e-9 >= silence_duration:
                    if active_time + 1e-9 >= min_speech_duration:
                        return np.concatenate(chunks, axis=0)
                    # Ignore isolated clicks without renewing the start timeout.
                    waiting_time += phrase_time
                    if waiting_time >= start_timeout:
                        raise NoSpeechError("Only brief sounds were detected; please speak a command.")
                    chunks.clear()
                    pre_roll.clear()
                    started = False
                    quiet_time = active_time = phrase_time = 0.0
                elif phrase_time + 1e-9 >= max_duration:
                    raise AudioQualityError(
                        "Recording reached its limit without a pause. Use a shorter command or reduce background noise."
                    )
    except (NoSpeechError, AudioQualityError):
        raise
    except sd.PortAudioError as error:
        raise MicrophoneUnavailableError(
            "Microphone capture failed. Check permissions and whether another app is using it."
        ) from error
