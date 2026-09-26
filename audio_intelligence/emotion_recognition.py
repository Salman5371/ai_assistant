"""Experimental speech emotion inference with a lazy, local SUPERB backend."""
from .preprocessing import preprocess


class EmotionRecognizer:
    """Backend signature: backend(mono_float32, sample_rate) -> application result.

    The caller owns model loading and label/confidence interpretation. No heuristic
    output is presented as a trained model prediction.
    """
    def __init__(self, backend=None, sample_rate=16000):
        self.backend = backend
        self.sample_rate = sample_rate

    def recognize(self, audio, sample_rate):
        if self.backend is None:
            raise RuntimeError("No emotion model configured. Supply a callable backend.")
        samples, rate = preprocess(audio, sample_rate, self.sample_rate)
        if not len(samples):
            raise ValueError("No non-silent audio to analyze")
        return self.backend(samples, rate)


MODEL_ID = "superb/wav2vec2-base-superb-er"
NOTICE = ("Experimental AI inference, not a psychological or medical diagnosis. "
          "Confidence is a model score, not certainty about your feelings.")
LABELS = {"neu": "neutral", "hap": "happy", "ang": "angry", "sad": "sad"}


class PretrainedEmotionRecognizer:
    """SUPERB Wav2Vec2: four-class English utterance classification on CPU.

    Model weights download only on load()/recognize(), then use Hugging Face's
    local cache. Captured audio is never sent to a remote inference service.
    """
    def __init__(self, *, local_files_only=False):
        self.local_files_only = local_files_only
        self._model = self._extractor = self._torch = None

    def load(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification
        except ImportError as error:
            raise RuntimeError(
                "Emotion recognition needs optional dependencies. Run: "
                "python -m pip install -r requirements-emotion.txt"
            ) from error
        try:
            options = dict(local_files_only=self.local_files_only, trust_remote_code=False)
            extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID, **options)
            model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_ID, **options)
            model.to("cpu")
            model.eval()
        except Exception as error:
            raise RuntimeError(
                "Could not load the speech emotion model. Check optional dependencies, "
                "disk space and internet access for the first download, or the local model cache."
            ) from error
        self._extractor, self._model, self._torch = extractor, model, torch

    def recognize(self, audio, sample_rate, *, top_k=3):
        import numpy as np
        from .preprocessing import to_mono, resample, validate_rate
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 4:
            raise ValueError("top_k must be an integer between 1 and 4")
        rate = validate_rate(sample_rate)
        samples = to_mono(audio)
        if not 0.5 <= len(samples) / rate <= 30:
            raise ValueError("Provide between 0.5 and 30 seconds of speech.")
        if float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) < 1e-5:
            raise ValueError("No audible speech to analyze.")
        samples = resample(samples, rate, 16000)
        self.load()
        # Follow the model feature extractor's normalization, not peak normalization.
        inputs = self._extractor(samples, sampling_rate=16000, return_tensors="pt", padding=True)
        with self._torch.inference_mode():
            logits = self._model(**inputs).logits
            scores = self._torch.softmax(logits, dim=-1)[0].cpu().tolist()
        if len(scores) != 4 or not all(np.isfinite(score) and 0 <= score <= 1 for score in scores):
            raise RuntimeError("Emotion model returned invalid scores.")
        predictions = []
        for index, score in enumerate(scores):
            label = self._model.config.id2label[index]
            if label not in LABELS:
                raise RuntimeError("Emotion model returned an unsupported label.")
            predictions.append({"emotion": LABELS[label], "confidence": float(score)})
        predictions.sort(key=lambda item: item["confidence"], reverse=True)
        return {"emotion": predictions[0]["emotion"],
                "confidence": predictions[0]["confidence"],
                "top_predictions": predictions[:top_k], "model": MODEL_ID,
                "experimental": True, "notice": NOTICE}


_default_recognizer = None


def analyze_voice_emotion():
    """Load before recording, then analyze a fresh, explicitly requested utterance."""
    global _default_recognizer
    from .recorder import record_until_silence
    if _default_recognizer is None:
        _default_recognizer = PretrainedEmotionRecognizer()
    print("Preparing speech emotion model; first use downloads model weights...")
    _default_recognizer.load()
    print("Speak a short sentence in English after the microphone prompt.")
    audio = record_until_silence(min_speech_duration=0.5)
    return _default_recognizer.recognize(audio, 16000)


def format_emotion_result(result):
    top = "; ".join(f"{item['emotion']} {item['confidence']:.1%}"
                    for item in result["top_predictions"])
    return (f"Predicted voice emotion: {result['emotion']}. "
            f"Confidence (model score): {result['confidence']:.1%}. "
            f"Top predictions: {top}. {NOTICE}")
