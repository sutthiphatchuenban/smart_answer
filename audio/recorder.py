import queue
import threading
import time
import numpy as np
import sounddevice as sd
from config import safe_print as print

from .processing import (
    get_audio_devices,
    resample_audio,
    reduce_noise_scipy,
    find_system_audio_device,
)

try:
    import pyaudiowpatch as pyaudio
    HAS_PYAUDIOWPATCH = True
except ImportError:
    HAS_PYAUDIOWPATCH = False


class AudioRecorder:
    def __init__(self, device_index=None, silence_threshold=0.01, silence_duration=1.5, noise_reduction_enabled=True, source_type="mic"):
        self.device_index = device_index
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.noise_reduction_enabled = noise_reduction_enabled
        self.source_type = source_type  # 'mic' or 'system'
        
        self.recording = False
        self.audio_queue = queue.Queue()
        self.thread = None
        self.mode = "manual"  # 'manual' or 'auto'
        self.current_recording = []
        self.volume_callback = None  # To update UI volume meter
        self.live_audio_callback = None  # To stream live audio chunks for real-time transcription
        self.calibration_callback = None  # callback(tuned_threshold)
        self.device_switch_callback = None  # callback(new_device_index) - called when auto-switching devices
        self.speech_status_callback = None  # callback(is_speaking) - called when VAD detects speech starts/stops
        self.background_noise_rms = 0.005  # running estimate of silent noise floor
        self.calibrating = False
        self.calibration_end_time = 0.0
        self.calibration_rms_values = []
        self.calibration_audio_chunks = []
        self.noise_profile = None
        self.smooth_rms = 0.0
        self.live_audio_lock = threading.Lock()
        self.live_audio_busy = False
        self.live_audio_interval = 2.0
        self.live_audio_max_seconds = 4.0
        
        # Max speech duration limit (seconds) to force-complete a chunk when interrupted/over-talking
        self.max_speech_duration = 12.0
        
        # Audio formatting
        self.target_samplerate = 16000
        
    def set_volume_callback(self, callback):
        self.volume_callback = callback
        
    def start(self, mode="manual"):
        if self.recording:
            return
        self.mode = mode
        self.recording = True
        self.current_recording = []
        self.calibration_audio_chunks = []
        self.noise_profile = None
        self.smooth_rms = 0.0
        
        # Always run a 1.2s silence calibration on start to build noise profile
        self.calibrating = True
        self.calibration_end_time = time.time() + 1.2
        self.calibration_rms_values = []
        print(f"Starting 1.2s silence/noise calibration on {mode} mode...")
        
        # Choose the right recording backend based on source type
        if self.source_type == "system" and HAS_PYAUDIOWPATCH:
            target = self._record_loop_wasapi
        else:
            target = self._record_loop
            
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()
        
    def stop(self):
        if not self.recording:
            return
        self.recording = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def _record_loop(self):
        devices = get_audio_devices()
        device_info = None
        
        # Resolve device
        if self.device_index is not None:
            for d in devices:
                if d['index'] == self.device_index:
                    device_info = d
                    break
        
        if device_info is None and devices:
            # Fallback to default input
            try:
                default_idx = sd.default.device[0]
                for d in devices:
                    if d['index'] == default_idx:
                        device_info = d
                        break
            except Exception:
                device_info = devices[0]
                
        if not device_info:
            print("No audio devices found to record from.")
            self.recording = False
            return
        
        # Skip pure loopback devices (0 input channels) - they can't be opened as InputStream
        if device_info.get('is_pure_loopback', False):
            print(f"Device '{device_info['desc']}' is a pure WASAPI loopback (0 input channels) and cannot be opened directly.")
            print("Searching for alternative system audio device (Stereo Mix preferred)...")
            alt_device = self._find_alternative_system_device(devices, device_info['index'])
            if alt_device:
                device_info = alt_device
                self.device_index = alt_device['index']
                print(f"Auto-switched to: {device_info['desc']}")
                if self.device_switch_callback:
                    self.device_switch_callback(alt_device['index'])
            else:
                print("ERROR: No usable system audio device found. Please enable 'Stereo Mix' in Windows Sound settings.")
                self.recording = False
                return
            
        samplerate = device_info['default_samplerate']
        channels = min(1, device_info['channels'])  # Try to record mono
        if device_info.get('is_loopback', False) and not device_info.get('is_pure_loopback', False):
            # Loopback recording often requires stereo or specific channel count
            channels = device_info['channels']
            
        # sounddevice stream setup
        chunk_duration = 0.1  # 100ms chunks
        blocksize = int(samplerate * chunk_duration)
        
        silence_samples_needed = int(self.silence_duration / chunk_duration)
        silent_chunks_count = 0
        has_speech = False
        speech_chunks_count = 0
        
        # Internal queue to pass raw audio from callback to processing thread
        self.raw_queue = queue.Queue()
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                pass
            self.raw_queue.put(indata.copy())
            
        # Try to open the stream; if all format attempts fail, try alternative devices
        stream, samplerate, channels, blocksize = self._try_open_stream(
            device_info, samplerate, channels, chunk_duration, blocksize, audio_callback
        )
        
        if stream is None:
            # Current device failed - try alternative devices
            print(f"All format attempts failed for '{device_info['desc']}'. Trying alternative devices...")
            alt_device = self._find_alternative_system_device(devices, device_info['index'])
            if alt_device:
                device_info = alt_device
                self.device_index = alt_device['index']
                samplerate = alt_device['default_samplerate']
                channels = min(1, alt_device['channels'])
                blocksize = int(samplerate * chunk_duration)
                print(f"Trying alternative device: {device_info['desc']}")
                stream, samplerate, channels, blocksize = self._try_open_stream(
                    device_info, samplerate, channels, chunk_duration, blocksize, audio_callback
                )
                if stream is not None and self.device_switch_callback:
                    self.device_switch_callback(alt_device['index'])
            
            if stream is None:
                print("ERROR: Could not open any audio device. Please check your audio settings.")
                self.recording = False
                return
            
        try:
            with stream:
                print(f"Started recording from {device_info['desc']} (Rate: {samplerate}Hz, Channels: {channels})")
                last_live_time = 0.0
                while self.recording:
                    try:
                        data = self.raw_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                        
                    # Convert to mono if stereo
                    if channels > 1:
                        mono_data = np.mean(data, axis=1)
                    else:
                        mono_data = data.flatten()
                        
                    # Calculate volume (RMS) using raw audio (extremely fast, no STFT in loop)
                    rms = np.sqrt(np.mean(mono_data**2)) if len(mono_data) > 0 else 0.0
                    
                    # Smooth RMS to prevent brief spikes from resetting silence detection
                    self.smooth_rms = 0.6 * self.smooth_rms + 0.4 * rms
                    
                    if self.volume_callback:
                        step = max(1, len(mono_data) // 32)
                        waveform_chunk = mono_data[::step][:32].tolist()
                        self.volume_callback(rms, waveform_chunk)
                        
                    if self.calibrating:
                        # Collect calibration noise chunks
                        self.calibration_audio_chunks.append(mono_data)
                        if time.time() < self.calibration_end_time:
                            self.calibration_rms_values.append(rms)
                        else:
                            # Calibration complete
                            if self.calibration_audio_chunks:
                                self.noise_profile = np.concatenate(self.calibration_audio_chunks)
                                
                            max_noise_rms = np.max(self.calibration_rms_values) if self.calibration_rms_values else 0.01
                            self.background_noise_rms = np.mean(self.calibration_rms_values) if self.calibration_rms_values else 0.005
                            # Smart autotune: never exceed 0.080 to ensure quiet voice triggers VAD, while staying above background hum
                            if max_noise_rms < 0.010:
                                self.silence_threshold = max_noise_rms + 0.008
                            elif max_noise_rms < 0.080:
                                self.silence_threshold = max_noise_rms + 0.006
                            else:
                                self.silence_threshold = 0.080
                            self.silence_threshold = max(0.003, min(0.080, self.silence_threshold))
                            
                            self.calibrating = False
                            print(f"Calibration complete. Autotuned silence threshold to: {self.silence_threshold:.3f}")
                            if self.calibration_callback:
                                self.calibration_callback(self.silence_threshold)
                            self.calibration_audio_chunks = []
                    else:
                        # Normal capture
                        if self.mode == "manual":
                            self.current_recording.append(mono_data)
                        else:
                            # Auto VAD Mode
                            if self.smooth_rms > self.silence_threshold:
                                if not has_speech:
                                    print("Speech detected, starting recording chunk...")
                                    has_speech = True
                                    speech_chunks_count = 0
                                    if self.speech_status_callback:
                                        self.speech_status_callback(True)
                                self.current_recording.append(mono_data)
                                silent_chunks_count = 0
                                speech_chunks_count += 1
                                
                                # Max speech duration check (force split if speaking too long without pauses/interrupted)
                                max_speech_chunks = int(self.max_speech_duration / chunk_duration)
                                if speech_chunks_count >= max_speech_chunks:
                                    print("Max speech duration reached. Force-completing chunk to analyze.")
                                    chunks_to_submit = list(self.current_recording)
                                    self.current_recording = []
                                    speech_chunks_count = 0
                                    silent_chunks_count = 0
                                    threading.Thread(
                                        target=self._submit_audio_async,
                                        args=(chunks_to_submit, samplerate, max_speech_chunks),
                                        daemon=True
                                    ).start()
                            else:
                                if has_speech:
                                    self.current_recording.append(mono_data)
                                    silent_chunks_count += 1
                                    
                                    # Silence threshold exceeded duration
                                    if silent_chunks_count >= silence_samples_needed:
                                        print("Silence detected, completing chunk.")
                                        chunks_to_submit = list(self.current_recording)
                                        self.current_recording = []
                                        has_speech = False
                                        if self.speech_status_callback:
                                            self.speech_status_callback(False)
                                        silent_chunks_count = 0
                                        threading.Thread(
                                            target=self._submit_audio_async,
                                            args=(chunks_to_submit, samplerate, speech_chunks_count),
                                            daemon=True
                                        ).start()
                                        speech_chunks_count = 0
                                else:
                                    # Slowly adapt background noise floor when silent
                                    self.background_noise_rms = 0.98 * self.background_noise_rms + 0.02 * rms
                                    # Auto adjust VAD threshold
                                    if self.background_noise_rms < 0.010:
                                        self.silence_threshold = self.background_noise_rms + 0.008
                                    elif self.background_noise_rms < 0.080:
                                        self.silence_threshold = self.background_noise_rms + 0.006
                                    else:
                                        self.silence_threshold = 0.080
                                    self.silence_threshold = max(0.003, min(0.080, self.silence_threshold))
                                
                    # Send live chunk for real-time transcription if speaking
                    current_time = time.time()
                    if self.live_audio_callback and (current_time - last_live_time > self.live_audio_interval) and self.current_recording and not self.calibrating:
                        last_live_time = current_time
                        self._queue_live_audio_preview(self.current_recording, samplerate)
                                
                    time.sleep(0.01)
                    
            # If manual mode stopped, submit whatever was recorded
            if self.mode == "manual" and self.current_recording:
                # In manual mode, we assume they intentionally started and stopped, so no spike filter needed (pass high value)
                chunks_to_submit = list(self.current_recording)
                self.current_recording = []
                threading.Thread(
                    target=self._submit_audio_async,
                    args=(chunks_to_submit, samplerate, 999),
                    daemon=True
                ).start()
                
        except Exception as e:
            print(f"Error in audio capture: {e}")
            self.recording = False
    
    def _try_open_stream(self, device_info, samplerate, channels, chunk_duration, blocksize, audio_callback):
        """Attempts to open an InputStream with format fallbacks. Returns (stream, samplerate, channels, blocksize) or (None,...) on failure."""
        try:
            stream = sd.InputStream(
                device=device_info['index'],
                channels=channels,
                samplerate=samplerate,
                blocksize=blocksize,
                dtype='float32',
                callback=audio_callback
            )
            return stream, samplerate, channels, blocksize
        except Exception as first_err:
            rates_to_try = [samplerate, 48000, 44100, 16000]
            channels_to_try = [2, 1, 6, 8]
            
            for rate in rates_to_try:
                for ch in channels_to_try:
                    if rate == samplerate and ch == channels:
                        continue
                    try:
                        print(f"Fallback attempt: trying device {device_info['index']} with Rate={rate}Hz, Channels={ch}...")
                        blocksize_fb = int(rate * chunk_duration)
                        stream = sd.InputStream(
                            device=device_info['index'],
                            channels=ch,
                            samplerate=rate,
                            blocksize=blocksize_fb,
                            dtype='float32',
                            callback=audio_callback
                        )
                        return stream, rate, ch, blocksize_fb
                    except Exception:
                        pass
            
            print(f"Could not open device {device_info['index']} ({device_info['desc']}): {first_err}")
            return None, samplerate, channels, blocksize
    
    def _find_alternative_system_device(self, devices, exclude_index):
        """Find an alternative system audio device, preferring Stereo Mix over WASAPI loopback."""
        # Priority 1: Stereo Mix (most reliable for system audio capture)
        for d in devices:
            if d['index'] == exclude_index:
                continue
            if "stereo mix" in d['name'].lower() and not d.get('is_pure_loopback', False):
                return d
        
        # Priority 2: Any non-pure-loopback system audio device  
        for d in devices:
            if d['index'] == exclude_index:
                continue
            if (d.get('is_loopback', False) or "stereo mix" in d['name'].lower()) and not d.get('is_pure_loopback', False):
                return d
        
        # Priority 3: Any device that can be opened as input
        for d in devices:
            if d['index'] == exclude_index:
                continue
            if not d.get('is_pure_loopback', False) and d.get('channels', 0) > 0:
                return d
        
        return None
    
    def _record_loop_wasapi(self):
        """Record system audio using PyAudioWPatch WASAPI loopback - reliable capture from speakers."""
        p = pyaudio.PyAudio()
        loopback_device = None
        try:
            # Try to resolve selected device from sounddevice to pyaudiowpatch
            if self.device_index is not None:
                try:
                    import sounddevice as sd
                    sd_dev = sd.query_devices(self.device_index)
                    sd_name = sd_dev['name']
                    # Look for matching loopback device in pyaudiowpatch
                    for i in range(p.get_device_count()):
                        dev_info = p.get_device_info_by_index(i)
                        if dev_info.get('isLoopbackDevice', False):
                            # Compare names (e.g. "Speakers (Realtek(R) Audio)" in "Speakers (Realtek(R) Audio) [Loopback]")
                            if sd_name.lower() in dev_info['name'].lower() or dev_info['name'].lower() in sd_name.lower():
                                loopback_device = dev_info
                                print(f"Matched selected device index {self.device_index} ({sd_name}) to WASAPI Loopback device: {loopback_device['name']} (index={i})")
                                break
                except Exception as e:
                    print(f"Could not map sounddevice index {self.device_index} to WASAPI loopback: {e}")
            
            # Fallback to default WASAPI loopback device
            if loopback_device is None:
                loopback_device = p.get_default_wasapi_loopback()
                print(f"WASAPI Loopback device (default): {loopback_device['name']}")
        except Exception as e:
            print(f"Could not find WASAPI loopback device: {e}")
            p.terminate()
            self.recording = False
            return
        
        channels = int(loopback_device['maxInputChannels'])
        samplerate = int(loopback_device['defaultSampleRate'])
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(samplerate * chunk_duration)
        
        silence_samples_needed = int(self.silence_duration / chunk_duration)
        silent_chunks_count = 0
        has_speech = False
        speech_chunks_count = 0
        
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=samplerate,
                input=True,
                input_device_index=loopback_device['index'],
                frames_per_buffer=chunk_size,
            )
            
            print(f"Started WASAPI loopback recording from {loopback_device['name']} (Rate: {samplerate}Hz, Channels: {channels})")
            last_live_time = 0.0
            
            while self.recording:
                try:
                    raw_data = stream.read(chunk_size, exception_on_overflow=False)
                except Exception as e:
                    if self.recording:
                        print(f"WASAPI read error: {e}")
                    break
                
                # Convert int16 bytes to float32 numpy array
                audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Convert to mono if stereo
                if channels > 1:
                    audio_np = audio_np.reshape(-1, channels)
                    mono_data = np.mean(audio_np, axis=1)
                else:
                    mono_data = audio_np
                
                # === Shared audio processing pipeline (same as _record_loop) ===
                
                # Calculate volume (RMS) using raw audio (extremely fast, no STFT in loop)
                rms = np.sqrt(np.mean(mono_data**2)) if len(mono_data) > 0 else 0.0
                
                # Smooth RMS
                self.smooth_rms = 0.6 * self.smooth_rms + 0.4 * rms
                
                if self.volume_callback:
                    step = max(1, len(mono_data) // 32)
                    waveform_chunk = mono_data[::step][:32].tolist()
                    self.volume_callback(rms, waveform_chunk)
                
                if self.calibrating:
                    self.calibration_audio_chunks.append(mono_data)
                    if time.time() < self.calibration_end_time:
                        self.calibration_rms_values.append(rms)
                    else:
                        if self.calibration_audio_chunks:
                            self.noise_profile = np.concatenate(self.calibration_audio_chunks)
                        
                        max_noise_rms = np.max(self.calibration_rms_values) if self.calibration_rms_values else 0.01
                        self.background_noise_rms = np.mean(self.calibration_rms_values) if self.calibration_rms_values else 0.005
                        # Smart autotune: never exceed 0.080 to ensure quiet voice triggers VAD, while staying above background hum
                        if max_noise_rms < 0.010:
                            self.silence_threshold = max_noise_rms + 0.008
                        elif max_noise_rms < 0.080:
                            self.silence_threshold = max_noise_rms + 0.006
                        else:
                            self.silence_threshold = 0.080
                        self.silence_threshold = max(0.003, min(0.080, self.silence_threshold))
                        
                        self.calibrating = False
                        print(f"Calibration complete. Autotuned silence threshold to: {self.silence_threshold:.3f}")
                        if self.calibration_callback:
                            self.calibration_callback(self.silence_threshold)
                        self.calibration_audio_chunks = []
                else:
                    # Normal capture
                    if self.mode == "manual":
                        self.current_recording.append(mono_data)
                    else:
                        # Auto VAD Mode
                        if self.smooth_rms > self.silence_threshold:
                            if not has_speech:
                                print("Speech detected, starting recording chunk...")
                                has_speech = True
                                speech_chunks_count = 0
                                if self.speech_status_callback:
                                    self.speech_status_callback(True)
                            self.current_recording.append(mono_data)
                            silent_chunks_count = 0
                            speech_chunks_count += 1
                            
                            # Max speech duration check (force split if speaking too long without pauses/interrupted)
                            max_speech_chunks = int(self.max_speech_duration / chunk_duration)
                            if speech_chunks_count >= max_speech_chunks:
                                print("Max speech duration reached. Force-completing chunk to analyze.")
                                chunks_to_submit = list(self.current_recording)
                                self.current_recording = []
                                speech_chunks_count = 0
                                silent_chunks_count = 0
                                threading.Thread(
                                    target=self._submit_audio_async,
                                    args=(chunks_to_submit, samplerate, max_speech_chunks),
                                    daemon=True
                                ).start()
                        else:
                            if has_speech:
                                self.current_recording.append(mono_data)
                                silent_chunks_count += 1
                                
                                if silent_chunks_count >= silence_samples_needed:
                                    print("Silence detected, completing chunk.")
                                    chunks_to_submit = list(self.current_recording)
                                    self.current_recording = []
                                    has_speech = False
                                    if self.speech_status_callback:
                                        self.speech_status_callback(False)
                                    silent_chunks_count = 0
                                    threading.Thread(
                                        target=self._submit_audio_async,
                                        args=(chunks_to_submit, samplerate, speech_chunks_count),
                                        daemon=True
                                    ).start()
                                    speech_chunks_count = 0
                            else:
                                # Slowly adapt background noise floor when silent
                                self.background_noise_rms = 0.98 * self.background_noise_rms + 0.02 * rms
                                # Auto adjust VAD threshold
                                if self.background_noise_rms < 0.010:
                                    self.silence_threshold = self.background_noise_rms + 0.008
                                elif self.background_noise_rms < 0.080:
                                    self.silence_threshold = self.background_noise_rms + 0.006
                                else:
                                    self.silence_threshold = 0.080
                                self.silence_threshold = max(0.003, min(0.080, self.silence_threshold))
                
                # Send live chunk for real-time transcription
                current_time = time.time()
                if self.live_audio_callback and (current_time - last_live_time > self.live_audio_interval) and self.current_recording and not self.calibrating:
                    last_live_time = current_time
                    self._queue_live_audio_preview(self.current_recording, samplerate)
            
            # If manual mode stopped, submit whatever was recorded
            if self.mode == "manual" and self.current_recording:
                chunks_to_submit = list(self.current_recording)
                self.current_recording = []
                threading.Thread(
                    target=self._submit_audio_async,
                    args=(chunks_to_submit, samplerate, 999),
                    daemon=True
                ).start()
                
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Error in WASAPI audio capture: {e}")
            self.recording = False
        finally:
            p.terminate()
            
    def _submit_audio_async(self, recording_chunks, source_samplerate, speech_chunks=0):
        if not recording_chunks:
            return
            
        # Reject short clicks and keyboard spikes
        # 1 chunk = 100ms. If sound is above threshold for less than 4 chunks (400ms), ignore as noise.
        if speech_chunks < 4:
            print(f"Noise spike detected (sound active for only {speech_chunks} chunks / {speech_chunks*100}ms). Ignoring.")
            return
            
        try:
            full_audio = np.concatenate(recording_chunks)
            
            # Avoid processing very short sounds (less than 0.8s of audio)
            if len(full_audio) < int(source_samplerate * 0.8):
                print("Audio chunk too short, ignoring.")
                return
                
            # Apply noise reduction to final audio
            if self.noise_reduction_enabled:
                profile = self.noise_profile.copy() if self.noise_profile is not None else None
                full_audio = reduce_noise_scipy(full_audio, source_samplerate, profile)
                
            resampled = resample_audio(full_audio, source_samplerate, self.target_samplerate)
            
            # Normalize audio level
            max_val = np.max(np.abs(resampled))
            if max_val > 0.001:
                resampled = resampled / max_val * 0.8  # Normalize to -2dB peak
                
            print(f"Submitting {len(resampled)/self.target_samplerate:.2f}s of denoised audio to queue.")
            self.audio_queue.put(resampled)
        except Exception as e:
            print(f"Error submitting audio in background: {e}")

    def _queue_live_audio_preview(self, recording_chunks, samplerate):
        if not self.live_audio_callback or not recording_chunks:
            return

        with self.live_audio_lock:
            if self.live_audio_busy:
                return
            self.live_audio_busy = True

        chunks_to_send = list(recording_chunks)

        def send_live_async():
            try:
                live_audio = np.concatenate(chunks_to_send)
                max_samples = int(samplerate * self.live_audio_max_seconds)
                if len(live_audio) > max_samples:
                    live_audio = live_audio[-max_samples:]

                if len(live_audio) >= int(samplerate * 0.5):
                    # Check if audio has sufficient volume to be speech (skip if too quiet)
                    live_rms = np.sqrt(np.mean(live_audio**2))
                    if live_rms < max(0.002, self.silence_threshold * 0.5):
                        return
                        
                    live_resampled = resample_audio(live_audio, samplerate, self.target_samplerate)
                    max_val = np.max(np.abs(live_resampled))
                    if max_val > 0.001:
                        live_resampled = live_resampled / max_val * 0.8
                    self.live_audio_callback(live_resampled)
            except Exception as e:
                print(f"Error in live audio preview: {e}")
            finally:
                with self.live_audio_lock:
                    self.live_audio_busy = False

        threading.Thread(target=send_live_async, daemon=True).start()
