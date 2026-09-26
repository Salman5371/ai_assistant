"""Reusable, headless audio plots and numerical features for a future UI.

No windows, microphone access, or file writes occur on import. Array input is
(frames,) or (frames, channels); spectral plots mix channels to mono.
"""
from pathlib import Path
import os
import tempfile
import numpy as np
from .preprocessing import as_float, to_mono, validate_rate


def _audio(audio, sample_rate):
    rate = validate_rate(sample_rate)
    data = as_float(audio)
    if not len(data):
        raise ValueError("Cannot visualize empty audio")
    if len(data) / rate > 600:
        raise ValueError("Visualize at most 10 minutes at a time")
    return data, rate


def _axes(ax):
    if ax is not None:
        return ax
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError as error:
        raise ImportError("Install plotting support: python -m pip install -r requirements-visualization.txt") from error
    figure = Figure(figsize=(10, 4), layout="constrained")
    FigureCanvasAgg(figure)
    return figure.subplots()


def spectrogram_data(audio, sample_rate, *, n_fft=1024, hop_length=256):
    """Return (times_seconds, frequencies_hz, power[frequency, time]).

    Hann-window STFT, with end padding so the final samples are included. Power
    is squared FFT magnitude divided by window energy, not calibrated sound SPL.
    """
    data, rate = _audio(audio, sample_rate)
    if isinstance(n_fft, bool) or not isinstance(n_fft, int) or not 16 <= n_fft <= 16384:
        raise ValueError("n_fft must be an integer from 16 to 16384")
    if isinstance(hop_length, bool) or not isinstance(hop_length, int) or not 1 <= hop_length <= n_fft:
        raise ValueError("hop_length must be an integer from 1 to n_fft")
    mono = to_mono(data)
    count = 1 + max(0, int(np.ceil((len(mono) - n_fft) / hop_length)))
    if count * (n_fft // 2 + 1) > 20_000_000:
        raise ValueError("Spectrogram is too large; shorten audio or increase hop_length")
    mono = np.pad(mono, (0, (count - 1) * hop_length + n_fft - len(mono)))
    window = np.hanning(n_fft)
    power = np.empty((n_fft // 2 + 1, count), dtype=np.float32)
    for start in range(0, count, 128):
        frames = np.arange(start, min(start + 128, count))[:, None] * hop_length + np.arange(n_fft)
        transformed = np.fft.rfft(mono[frames] * window, axis=1)
        power[:, start:start + len(frames)] = (np.abs(transformed) ** 2 / np.sum(window ** 2)).T
    times = (np.arange(count) * hop_length + n_fft / 2) / rate
    return times, np.fft.rfftfreq(n_fft, 1 / rate), power


def mel_spectrogram_data(audio, sample_rate, *, n_fft=1024, hop_length=256,
                         n_mels=64, fmin=0.0, fmax=None):
    """Return (times, Mel-band centers in Hz, Mel-band power).

    Uses HTK Mel conversion and triangular filters, without area normalization.
    """
    rate = validate_rate(sample_rate)
    fmax = rate / 2 if fmax is None else fmax
    if not np.isfinite([fmin, fmax]).all() or not 0 <= fmin < fmax <= rate / 2:
        raise ValueError("Require 0 <= fmin < fmax <= Nyquist frequency")
    if isinstance(n_mels, bool) or not isinstance(n_mels, int) or not 2 <= n_mels <= 256:
        raise ValueError("n_mels must be an integer from 2 to 256")
    times, frequencies, power = spectrogram_data(audio, rate, n_fft=n_fft, hop_length=hop_length)
    mel_edges = np.linspace(2595 * np.log10(1 + fmin / 700),
                            2595 * np.log10(1 + fmax / 700), n_mels + 2)
    edges = 700 * (10 ** (mel_edges / 2595) - 1)
    rising = (frequencies[None, :] - edges[:-2, None]) / (edges[1:-1] - edges[:-2])[:, None]
    falling = (edges[2:, None] - frequencies[None, :]) / (edges[2:] - edges[1:-1])[:, None]
    filters = np.maximum(0, np.minimum(rising, falling))
    if np.any(filters.sum(axis=1) == 0):
        raise ValueError("Empty Mel bands; increase n_fft or reduce n_mels")
    return times, edges[1:-1], (filters @ power).astype(np.float32)


def power_to_db(power, *, dynamic_range=80.0):
    """Relative dB: maximum is 0 dB; all-zero input is at the display floor."""
    if not np.isfinite(dynamic_range) or dynamic_range <= 0:
        raise ValueError("dynamic_range must be finite and positive")
    power = np.asarray(power, dtype=np.float64)
    if not power.size or not np.isfinite(power).all() or np.any(power < 0):
        raise ValueError("Power must be a nonempty finite, nonnegative array")
    maximum = float(power.max())
    if maximum == 0:
        return np.full_like(power, -dynamic_range)
    return np.maximum(10 * np.log10(np.maximum(power / maximum, 1e-30)), -dynamic_range)


def plot_waveform(audio, sample_rate, *, ax=None, title="Audio waveform"):
    data, rate = _audio(audio, sample_rate)
    ax = _axes(ax)
    ax.plot(np.arange(len(data)) / rate, data, linewidth=0.7)
    ax.set(xlabel="Time (seconds)", ylabel="Amplitude (full scale)", title=title)
    ax.grid(True, alpha=0.25)
    return ax


def _plot_power(times, frequencies, power, rate, hop_length, ax, title, mel=False):
    ax = _axes(ax)
    image = ax.imshow(power_to_db(power), origin="lower", aspect="auto", cmap="magma",
                      vmin=-80, vmax=0,
                      extent=(max(0, times[0] - hop_length / (2 * rate)),
                              times[-1] + hop_length / (2 * rate), 0, len(frequencies)))
    indices = np.unique(np.linspace(0, len(frequencies) - 1, 6).astype(int))
    ax.set_yticks(indices + .5, [f"{frequencies[i]:.0f}" for i in indices])
    ax.set(xlabel="Time (seconds)", ylabel="Frequency (Hz, Mel spacing)" if mel else "Frequency (Hz)", title=title)
    ax.figure.colorbar(image, ax=ax, label="Power (dB relative to clip maximum)")
    return ax


def plot_spectrogram(audio, sample_rate, *, ax=None, title="Spectrogram", n_fft=1024, hop_length=256):
    times, frequencies, power = spectrogram_data(audio, sample_rate, n_fft=n_fft, hop_length=hop_length)
    return _plot_power(times, frequencies, power, sample_rate, hop_length, ax, title)


def plot_mel_spectrogram(audio, sample_rate, *, ax=None, title="Mel-spectrogram",
                         n_fft=1024, hop_length=256, n_mels=64, fmin=0.0, fmax=None):
    times, frequencies, power = mel_spectrogram_data(audio, sample_rate, n_fft=n_fft,
        hop_length=hop_length, n_mels=n_mels, fmin=fmin, fmax=fmax)
    return _plot_power(times, frequencies, power, sample_rate, hop_length, ax, title, mel=True)


def save_plot(ax, output_dir, *, name="audio", dpi=150):
    """Save a unique PNG in an existing directory, without overwriting any file.

    Names are filename components, never paths. Failed writes remove only the
    newly allocated output. Returns an absolute Path. Caller owns the axes.
    """
    import re
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", name):
        raise ValueError("name must be a simple 1-80 character filename stem")
    if isinstance(dpi, bool) or not isinstance(dpi, int) or not 50 <= dpi <= 600:
        raise ValueError("dpi must be an integer from 50 to 600")
    directory = Path(output_dir).resolve(strict=True)
    if not directory.is_dir():
        raise ValueError("output_dir must be an existing directory")
    descriptor, filename = tempfile.mkstemp(prefix=name + "-", suffix=".png", dir=directory)
    path = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            ax.figure.savefig(stream, format="png", dpi=dpi)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def generate_audio_plots(audio, sample_rate, output_dir, *, name="audio"):
    """Save three PNGs and return {waveform, spectrogram, mel_spectrogram: Path}.

    Rolls back files created by this call if any plot fails. No GUI or pyplot
    global state is used; figures are cleared after saving.
    """
    paths = {}
    try:
        for kind, plotter in (("waveform", plot_waveform), ("spectrogram", plot_spectrogram),
                              ("mel_spectrogram", plot_mel_spectrogram)):
            ax = plotter(audio, sample_rate)
            try:
                paths[kind] = save_plot(ax, output_dir, name=f"{name}-{kind}")
            finally:
                ax.figure.clear()
    except BaseException:
        for path in paths.values():
            path.unlink(missing_ok=True)
        raise
    return paths


def generate_wav_plots(wav_path, output_dir, *, name="audio"):
    """Visualize a local/uploaded PCM WAV without changing the input file."""
    import wave
    from .recorder import read_wav
    with wave.open(str(wav_path), "rb") as wav:
        if wav.getnframes() / wav.getframerate() > 600:
            raise ValueError("Visualize at most 10 minutes at a time")
        if wav.getnframes() * wav.getnchannels() * wav.getsampwidth() > 128 * 1024 * 1024:
            raise ValueError("Decoded WAV exceeds 128 MiB")
    audio, rate = read_wav(wav_path)
    return generate_audio_plots(audio, rate, output_dir, name=name)
