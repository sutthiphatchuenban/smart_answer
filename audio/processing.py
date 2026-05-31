import numpy as np
import sounddevice as sd
import scipy.signal


def get_audio_devices():
    """Queries and returns a list of input and WASAPI loopback audio devices."""
    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
    except Exception as e:
        print(f"Error querying audio devices: {e}")
        return []
        
    input_devices = []
    for i, d in enumerate(devices):
        try:
            api_name = hostapis[d['hostapi']]['name']
            max_in = d.get('max_input_channels', 0)
            max_out = d.get('max_output_channels', 0)
            
            # Identify standard inputs and WASAPI loopbacks (outputs we can record)
            is_input = max_in > 0
            is_wasapi_loopback = (api_name == "Windows WASAPI" and max_out > 0)
            # Pure loopback = WASAPI output device with 0 input channels.
            # These CANNOT be opened as InputStream by sounddevice and will always fail.
            is_pure_loopback = is_wasapi_loopback and not is_input
            
            if is_input or is_wasapi_loopback:
                # Determine channels to use
                channels = max_in if is_input else max_out
                desc = f"{d['name']} ({api_name})"
                if is_pure_loopback:
                    desc += " [Loopback]"
                    
                input_devices.append({
                    "index": i,
                    "name": d['name'],
                    "desc": desc,
                    "api": api_name,
                    "channels": channels,
                    "default_samplerate": int(d['default_samplerate']),
                    "is_loopback": is_wasapi_loopback,
                    "is_pure_loopback": is_pure_loopback,
                })
        except Exception as e:
            print(f"Error parsing device {i}: {e}")
    return input_devices


def resample_audio(audio_data, orig_sr, target_sr=16000):
    """Resamples audio data from orig_sr to target_sr using scipy."""
    if orig_sr == target_sr:
        return audio_data
    num_samples = int(len(audio_data) * target_sr / orig_sr)
    try:
        return scipy.signal.resample(audio_data, num_samples).astype(np.float32)
    except Exception as e:
        # Fallback simple linear interpolation if scipy resample fails
        print(f"Scipy resample failed: {e}. Using linear interpolation.")
        x_orig = np.linspace(0, len(audio_data), len(audio_data))
        x_target = np.linspace(0, len(audio_data), num_samples)
        return np.interp(x_target, x_orig, audio_data).astype(np.float32)


def reduce_noise_scipy(audio_data, samplerate, noise_profile=None):
    """
    Applies Short-Time Fourier Transform (STFT) spectral subtraction to reduce background noise.
    """
    if len(audio_data) < 512:
        return audio_data
        
    nperseg = 512
    noverlap = 384
    
    # Compute STFT
    try:
        f, t, Zxx = scipy.signal.stft(audio_data, fs=samplerate, nperseg=nperseg, noverlap=noverlap)
    except Exception as e:
        print(f"Error computing STFT: {e}")
        return audio_data
        
    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)
    
    # Estimate noise magnitude spectrum
    if noise_profile is not None and len(noise_profile) >= nperseg:
        try:
            _, _, Zxx_noise = scipy.signal.stft(noise_profile, fs=samplerate, nperseg=nperseg, noverlap=noverlap)
            noise_mu = np.mean(np.abs(Zxx_noise), axis=1, keepdims=True)
        except Exception:
            num_noise_frames = min(5, magnitude.shape[1])
            noise_mu = np.mean(magnitude[:, :num_noise_frames], axis=1, keepdims=True) if num_noise_frames > 0 else np.zeros((magnitude.shape[0], 1))
    else:
        # Fallback to estimating from first 5 frames of signal
        num_noise_frames = min(5, magnitude.shape[1])
        noise_mu = np.mean(magnitude[:, :num_noise_frames], axis=1, keepdims=True) if num_noise_frames > 0 else np.zeros((magnitude.shape[0], 1))
        
    # Subtract noise magnitude (oversubtraction alpha=2.0, spectral floor beta=0.03)
    alpha = 2.0
    beta = 0.03
    magnitude_clean = magnitude - alpha * noise_mu
    
    # Apply spectral floor
    floor = beta * magnitude
    magnitude_clean = np.maximum(magnitude_clean, floor)
    
    # Reconstruct complex spectrogram
    Zxx_clean = magnitude_clean * np.exp(1j * phase)
    
    # Perform ISTFT
    try:
        _, clean_audio = scipy.signal.istft(Zxx_clean, fs=samplerate, nperseg=nperseg, noverlap=noverlap)
    except Exception as e:
        print(f"Error computing ISTFT: {e}")
        return audio_data
        
    # Crop/pad clean_audio to the original length
    if len(clean_audio) > len(audio_data):
        clean_audio = clean_audio[:len(audio_data)]
    elif len(clean_audio) < len(audio_data):
        clean_audio = np.pad(clean_audio, (0, len(audio_data) - len(clean_audio)))
        
    return clean_audio.astype(np.float32)


def find_system_audio_device():
    """Finds the best device to capture computer speaker output.
    Prioritizes Stereo Mix (reliable, works as regular input) over WASAPI loopback."""
    devices = get_audio_devices()
    # 1. Try to find "Stereo Mix" (simplest, most reliable driver-level loopback)
    for d in devices:
        if "stereo mix" in d["name"].lower() and not d.get("is_pure_loopback", False):
            return d["index"]
            
    # 2. Try to find a WASAPI Speakers loopback device that has input channels
    for d in devices:
        if d["is_loopback"] and not d.get("is_pure_loopback", False) and "speaker" in d["name"].lower() and d["api"] == "Windows WASAPI":
            return d["index"]
            
    # 3. Try to find any WASAPI loopback device with input channels
    for d in devices:
        if d["is_loopback"] and not d.get("is_pure_loopback", False) and d["api"] == "Windows WASAPI":
            return d["index"]
    
    # 4. Last resort: pure loopback (will likely fail, but let the stream-open fallback handle it)
    for d in devices:
        if d["is_loopback"] and d["api"] == "Windows WASAPI":
            return d["index"]
            
    return None


def find_default_microphone_device():
    """Finds the default microphone device index."""
    devices = get_audio_devices()
    try:
        default_idx = sd.default.device[0]
        for d in devices:
            if d["index"] == default_idx:
                return d["index"]
    except Exception:
        pass
        
    # Fallback to the first non-loopback device
    for d in devices:
        if not d["is_loopback"]:
            return d["index"]
            
    return None
