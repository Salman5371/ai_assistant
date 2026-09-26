"""Audio arrays use float32 full-scale units, shaped (frames,) or (frames, channels)."""
import math
import numpy as np


def validate_rate(rate):
    if isinstance(rate, bool) or not isinstance(rate, (int, np.integer)) or rate <= 0:
        raise ValueError("sample rate must be a positive integer")
    return int(rate)


def as_float(audio):
    """Convert signed PCM or unsigned 8-bit PCM to floating full-scale units."""
    data = np.asarray(audio)
    if data.ndim not in (1, 2) or (data.ndim == 2 and data.shape[1] == 0):
        raise ValueError("audio must have shape (frames,) or (frames, channels)")
    if data.dtype.kind == "i":
        data = data.astype(np.float64) / (2 ** (data.dtype.itemsize * 8 - 1))
    elif data.dtype == np.uint8:
        data = (data.astype(np.float64) - 128) / 128
    elif data.dtype.kind != "f":
        raise ValueError("audio must be floating point, signed PCM, or uint8 PCM")
    if not np.isfinite(data).all():
        raise ValueError("audio contains non-finite samples")
    if np.any(np.abs(data) > np.finfo(np.float32).max):
        raise ValueError("audio exceeds float32 range")
    return data.astype(np.float32, copy=True)


def to_mono(audio):
    data = as_float(audio)
    return data.mean(axis=1, dtype=np.float64).astype(np.float32) if data.ndim == 2 else data


def normalize(audio, peak=0.95):
    """Peak normalization; silence remains silence. Does not mutate input."""
    if not math.isfinite(peak) or not 0 < peak <= 1:
        raise ValueError("peak must be in (0, 1]")
    data = as_float(audio)
    maximum = float(np.max(np.abs(data))) if data.size else 0
    return (data.astype(np.float64) * (peak / maximum)).astype(np.float32) if maximum else data


def trim_silence(audio, threshold_db=-40.0):
    """Trim leading/trailing samples below an absolute dBFS threshold.

    Internal pauses are retained. This is amplitude trimming, not voice detection.
    All-silent audio returns an empty array with the original channel shape.
    """
    if not math.isfinite(threshold_db) or threshold_db > 0:
        raise ValueError("threshold_db must be finite and <= 0")
    data = as_float(audio)
    level = np.max(np.abs(data), axis=1) if data.ndim == 2 else np.abs(data)
    active = np.flatnonzero(level > 10 ** (threshold_db / 20))
    return data[active[0]:active[-1] + 1].copy() if active.size else data[:0].copy()


def resample(audio, source_rate, target_rate):
    """Windowed-sinc resampling with anti-alias filtering; supports mono/stereo.

    Processes bounded blocks without a SciPy dependency. Output length is rounded
    to the nearest frame; edges extend the nearest input sample.
    """
    source_rate, target_rate = validate_rate(source_rate), validate_rate(target_rate)
    data = as_float(audio)
    if source_rate == target_rate or not len(data):
        return data
    count = round(len(data) * target_rate / source_rate)
    output = np.empty((count,) + data.shape[1:], dtype=np.float32)
    cutoff = min(1.0, target_rate / source_rate) * 0.94
    radius = math.ceil(16 / cutoff)
    offsets = np.arange(-radius, radius + 1)
    for start in range(0, count, 256):
        positions = np.arange(start, min(start + 256, count)) * source_rate / target_rate
        indices = np.floor(positions).astype(np.int64)[:, None] + offsets
        distances = positions[:, None] - indices
        weights = cutoff * np.sinc(cutoff * distances)
        weights *= np.where(np.abs(distances) <= radius,
                            0.5 + 0.5 * np.cos(np.pi * distances / radius), 0)
        weights /= weights.sum(axis=1, keepdims=True)
        samples = data[np.clip(indices, 0, len(data) - 1)]
        if data.ndim == 2:
            weights = weights[:, :, None]
        output[start:start + len(positions)] = (samples * weights).sum(axis=1)
    return output


def preprocess(audio, sample_rate, target_rate=16000, *, peak=0.95, threshold_db=-40.0):
    """Mono -> resample -> trim -> normalize. Return (samples, target_rate)."""
    data = resample(to_mono(audio), sample_rate, target_rate)
    return normalize(trim_silence(data, threshold_db), peak), validate_rate(target_rate)
