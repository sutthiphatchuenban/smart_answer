"""Test WASAPI loopback capture via PyAudioWPatch"""
import pyaudiowpatch as pyaudio
import numpy as np
import time
import wave
import io

p = pyaudio.PyAudio()

print("=== WASAPI Loopback Devices ===")
wasapi_info = None
for i in range(p.get_host_api_count()):
    api = p.get_host_api_info_by_index(i)
    if api["name"] == "Windows WASAPI":
        wasapi_info = api
        break

if not wasapi_info:
    print("No WASAPI host API found!")
    p.terminate()
    exit()

print(f"WASAPI host API index: {wasapi_info['index']}")
print(f"WASAPI device count: {wasapi_info['deviceCount']}")
print()

# Find the default loopback device (speakers)
default_speakers = None
loopback_device = None

try:
    default_speakers = p.get_default_wasapi_loopback()
    print(f"Default WASAPI Loopback: {default_speakers['name']}")
    print(f"  Index: {default_speakers['index']}")
    print(f"  Channels: {default_speakers['maxInputChannels']}")
    print(f"  Sample Rate: {int(default_speakers['defaultSampleRate'])}")
    loopback_device = default_speakers
except Exception as e:
    print(f"Could not get default loopback: {e}")
    # Try to find manually
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev.get('hostApi') == wasapi_info['index'] and dev.get('isLoopbackDevice', False):
            print(f"Found loopback device: {dev['name']} (index={i})")
            loopback_device = dev
            break

if not loopback_device:
    print("No loopback device found!")
    p.terminate()
    exit()

# Record 3 seconds from the loopback device
channels = int(loopback_device['maxInputChannels'])
rate = int(loopback_device['defaultSampleRate'])
chunk_size = 1024

print(f"\nRecording 3s from loopback... (play audio in Chrome now!)")
print(f"  Channels: {channels}, Rate: {rate}")

frames = []
try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=loopback_device['index'],
        frames_per_buffer=chunk_size,
    )
    
    total_frames = int(rate / chunk_size * 3.0)
    for i in range(total_frames):
        data = stream.read(chunk_size, exception_on_overflow=False)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    
    # Analyze captured audio
    all_data = b''.join(frames)
    audio_np = np.frombuffer(all_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    if channels > 1:
        # Mix to mono
        audio_np = audio_np.reshape(-1, channels).mean(axis=1)
    
    rms = np.sqrt(np.mean(audio_np**2))
    max_val = np.max(np.abs(audio_np))
    nonzero = np.count_nonzero(audio_np)
    
    print(f"\n=== Results ===")
    print(f"Total samples (mono): {len(audio_np)}")
    print(f"Non-zero samples: {nonzero} / {len(audio_np)} ({nonzero/len(audio_np)*100:.1f}%)")
    print(f"RMS: {rms:.6f}")
    print(f"Max: {max_val:.6f}")
    
    if rms > 0.01:
        print(f"\n✅ WASAPI Loopback is WORKING! Audio captured successfully!")
    elif rms > 0.001:
        print(f"\n⚠️ Low audio level but detectable. Turn up Chrome volume?")
    else:
        print(f"\n❌ No audio captured. Make sure something is playing in Chrome!")

except Exception as e:
    print(f"Error: {e}")

p.terminate()
