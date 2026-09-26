"""Audio event adapters and optional, lazily downloaded pretrained AST inference."""
from .preprocessing import preprocess


class AudioEventClassifier:
    """Backend signature: backend(mono_float32, sample_rate) -> application result.

    The caller owns model loading and label/confidence interpretation. No heuristic
    output is presented as a trained model prediction.
    """
    def __init__(self, backend=None, sample_rate=16000):
        self.backend = backend
        self.sample_rate = sample_rate

    def classify(self, audio, sample_rate):
        if self.backend is None:
            raise RuntimeError("No audio event model configured. Supply a callable backend.")
        samples, rate = preprocess(audio, sample_rate, self.sample_rate)
        if not len(samples):
            raise ValueError("No non-silent audio to analyze")
        return self.backend(samples, rate)


MODEL_ID = "MIT/ast-finetuned-audioset-10-10-0.4593"
MODEL_REVISION = "f826b80d28226b62986cc218e5cec390b1096902"


class PretrainedAudioEventClassifier:
    """Local inference using MIT's pretrained AudioSet AST via Transformers.

    No training or fine-tuning is performed. Scores are independent sigmoid
    outputs, aggregated by maximum over ten-second windows, not probabilities
    that must sum to one. No speech-specific trimming is applied.
    """
    def __init__(self, *, local_files_only=False):
        self.local_files_only = local_files_only
        self._model = self._extractor = self._torch = None

    def load(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import ASTFeatureExtractor, ASTForAudioClassification
        except ImportError as error:
            raise RuntimeError("Install optional audio-event dependencies: python -m pip install -r requirements-audio-events.txt") from error
        try:
            options = dict(revision=MODEL_REVISION, local_files_only=self.local_files_only,
                           trust_remote_code=False)
            extractor = ASTFeatureExtractor.from_pretrained(MODEL_ID, **options)
            model = ASTForAudioClassification.from_pretrained(MODEL_ID, use_safetensors=True, **options)
            model.to("cpu")
            model.eval()
        except Exception as error:
            raise RuntimeError("Could not load the audio-event model. Check dependencies, disk space, internet for the first download, or the local model cache.") from error
        self._extractor, self._model, self._torch = extractor, model, torch

    def classify(self, audio, sample_rate, *, top_k=5):
        import numpy as np
        from .preprocessing import to_mono, resample, validate_rate
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 3 <= top_k <= 5:
            raise ValueError("top_k must be 3, 4, or 5")
        rate = validate_rate(sample_rate)
        samples = to_mono(audio)
        if not 0.1 <= len(samples) / rate <= 60:
            raise ValueError("Provide 0.1 to 60 seconds of audio.")
        if np.max(np.abs(samples)) < 1e-5:
            raise ValueError("Audio is empty or silent; no sound category was predicted.")
        samples = resample(samples, rate, 16000)
        self.load()
        scores = None
        windows = 0
        for start in range(0, len(samples), 160000):
            chunk = samples[start:start + 160000]
            # Pad a very short final window so the feature extractor can frame it.
            if len(chunk) < 400:
                chunk = np.pad(chunk, (0, 400 - len(chunk)))
            inputs = self._extractor(chunk, sampling_rate=16000, return_tensors="pt")
            with self._torch.inference_mode():
                logits = self._model(**inputs).logits
                values = np.asarray(self._torch.sigmoid(logits)[0].cpu().tolist(), dtype=float)
            if (values.ndim != 1 or len(values) != len(self._model.config.id2label)
                    or len(values) < top_k or not np.isfinite(values).all()
                    or np.any((values < 0) | (values > 1))):
                raise RuntimeError("Audio-event model returned invalid scores.")
            scores = values if scores is None else np.maximum(scores, values)
            windows += 1
        indices = np.argsort(-scores, kind="stable")[:top_k]
        predictions = [{"category": self._model.config.id2label[int(index)],
                        "confidence": float(scores[index])} for index in indices]
        return {"category": predictions[0]["category"], "confidence": predictions[0]["confidence"],
                "top_predictions": predictions, "model": MODEL_ID, "revision": MODEL_REVISION,
                "windows": windows, "aggregation": "maximum sigmoid score across 10-second windows"}

    def classify_wav(self, path, *, top_k=5):
        import wave
        from .recorder import read_wav
        # Reject oversized inputs before reading their sample data into memory.
        with wave.open(str(path), "rb") as wav:
            if not 0.1 <= wav.getnframes() / wav.getframerate() <= 60:
                raise ValueError("WAV input must contain 0.1 to 60 seconds of audio.")
            if wav.getnframes() * wav.getnchannels() * wav.getsampwidth() > 64 * 1024 * 1024:
                raise ValueError("Decoded WAV input exceeds 64 MiB.")
        samples, rate = read_wav(path)
        return self.classify(samples, rate, top_k=top_k)

    def classify_microphone(self, *, duration=10.0, device=None, top_k=5):
        import math
        from .recorder import check_microphone, record_audio
        if not math.isfinite(duration) or not 0.1 <= duration <= 60:
            raise ValueError("Recording duration must be 0.1 to 60 seconds.")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 3 <= top_k <= 5:
            raise ValueError("top_k must be 3, 4, or 5")
        check_microphone(16000, device=device)
        self.load()
        print(f"Recording surrounding sounds for {duration:g} seconds...")
        samples = record_audio(duration, 16000, channels=1, device=device)
        return self.classify(samples, 16000, top_k=top_k)


_default_classifier = None


def analyze_audio_events(path=None):
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = PretrainedAudioEventClassifier()
    return (_default_classifier.classify_microphone() if path is None
            else _default_classifier.classify_wav(path))


def format_event_result(result):
    predictions = "; ".join(f"{item['category']}: {item['confidence']:.1%}"
                            for item in result["top_predictions"])
    return (f"Top predicted sound: {result['category']}. Confidence (model score): "
            f"{result['confidence']:.1%}. Top predictions: {predictions}. "
            "Pretrained model inference; scores may be wrong and do not sum to 100 percent.")
