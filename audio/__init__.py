"""Audio capture, processing, and device management package."""

from .recorder import AudioRecorder
from .processing import (
    get_audio_devices,
    resample_audio,
    reduce_noise_scipy,
    find_system_audio_device,
    find_default_microphone_device,
)

__all__ = [
    "AudioRecorder",
    "get_audio_devices",
    "resample_audio",
    "reduce_noise_scipy",
    "find_system_audio_device",
    "find_default_microphone_device",
]
