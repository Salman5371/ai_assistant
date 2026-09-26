"""Local audio utilities. No recording, model loading, or file writes on import."""
from .recorder import record_audio, record_wav, read_wav, write_wav, temporary_wav
from .preprocessing import preprocess, to_mono, resample, normalize, trim_silence

__all__ = ["record_audio", "record_wav", "read_wav", "write_wav", "temporary_wav",
           "preprocess", "to_mono", "resample", "normalize", "trim_silence"]

from .recorder import record_until_silence, check_microphone
__all__ += ["record_until_silence", "check_microphone"]
