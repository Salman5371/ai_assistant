"""Repeatable wall-clock latency measurement. Never computes task accuracy."""
import argparse
import json
import math
import platform
import statistics
import time
from pathlib import Path


def measure_latency(operation, *, runs=3, warmup=0, name="inference", audio_seconds=None):
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 1:
        raise ValueError("runs must be a positive integer")
    if isinstance(warmup, bool) or not isinstance(warmup, int) or warmup < 0:
        raise ValueError("warmup must be a nonnegative integer")
    if audio_seconds is not None and (not math.isfinite(audio_seconds) or audio_seconds <= 0):
        raise ValueError("audio_seconds must be positive and finite")
    warmup_timings = []
    for index in range(warmup):
        start = time.perf_counter()
        try:
            operation()
        except Exception as error:
            raise RuntimeError(f"Warmup {index + 1} failed ({type(error).__name__}); no measured report produced") from error
        warmup_timings.append(time.perf_counter() - start)
    timings, failures = [], []
    for index in range(runs):
        start = time.perf_counter()
        try:
            operation()
        except Exception as error:
            failures.append({"run": index + 1, "error_type": type(error).__name__})
        else:
            timings.append(time.perf_counter() - start)
    report = {"name": name, "requested_runs": runs, "successful_runs": len(timings),
              "warmup_runs": warmup, "warmup_seconds": warmup_timings, "latency_seconds": timings, "failures": failures,
              "python": platform.python_version(), "platform": platform.platform(),
              "scope": "wall-clock call latency only; no accuracy or F1 evaluated"}
    if timings:
        report.update(mean_seconds=statistics.mean(timings), median_seconds=statistics.median(timings),
                      min_seconds=min(timings), max_seconds=max(timings))
        if audio_seconds is not None:
            report["audio_seconds"] = audio_seconds
            report["mean_real_time_factor"] = statistics.mean(timings) / audio_seconds
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=("whisper", "google", "emotion", "events"))
    parser.add_argument("wav", type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.runs < 1 or args.warmup < 0:
        parser.error("--runs must be positive and --warmup must be nonnegative")
    if args.output and args.output.exists():
        parser.error("--output already exists; choose a new filename")
    from audio_intelligence.recorder import read_wav
    samples, rate = read_wav(args.wav)
    if len(samples) == 0:
        raise ValueError("Cannot evaluate empty audio")
    load_seconds = None
    if args.task in {"whisper", "google"}:
        from voice.stt import _transcribe_whisper, _transcribe_google
        from audio_intelligence.preprocessing import to_mono
        import numpy as np
        pcm = np.clip(np.rint(to_mono(samples).astype(float) * 32768), -32768, 32767).astype(np.int16)[:, None]
        # Direct backend calls prevent silently timing a fallback as Whisper.
        backend = _transcribe_whisper if args.task == "whisper" else _transcribe_google
        def operation():
            text = backend(pcm, rate)
            if not text:
                raise RuntimeError("No transcription returned")
    else:
        if args.task == "emotion":
            from audio_intelligence.emotion_recognition import PretrainedEmotionRecognizer
            model = PretrainedEmotionRecognizer()
            operation = lambda: model.recognize(samples, rate)
        else:
            from audio_intelligence.audio_event_classifier import PretrainedAudioEventClassifier
            model = PretrainedAudioEventClassifier()
            operation = lambda: model.classify(samples, rate)
        start = time.perf_counter()
        model.load()
        load_seconds = time.perf_counter() - start
    report = measure_latency(operation, runs=args.runs, warmup=args.warmup,
                             name=args.task, audio_seconds=len(samples) / rate)
    report["model_load_seconds"] = load_seconds
    report["timing_notes"] = "Audio decoding excluded. Model wrappers include preprocessing. STT includes preprocessing/network where applicable; warmup may include initial model download/load."
    serialized = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as file:
            file.write(serialized + "\n")
    print(serialized)
    if report["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
