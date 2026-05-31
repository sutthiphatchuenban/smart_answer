import sounddevice as sd
import numpy as np
import time

DEVICE_INDEX = 14  # Stereo Mix
SAMPLERATE = 48000
CHANNELS = 1
DURATION = 3.0

print(f"Recording {DURATION}s from device {DEVICE_INDEX} (play some audio in Chrome!)...")
print("Make sure YouTube/Chrome is playing audio NOW!")
time.sleep(1)

recording = sd.rec(int(DURATION * SAMPLERATE), 
                   samplerate=SAMPLERATE, 
                   channels=CHANNELS, 
                   device=DEVICE_INDEX,
                   dtype='float32')
sd.wait()

data = recording.flatten()
print(f"\nRecording shape: {recording.shape}")
print(f"Data type: {data.dtype}")
print(f"Data range: min={np.nanmin(data):.8f}, max={np.nanmax(data):.8f}")
print(f"Non-zero samples: {np.count_nonzero(data)} / {len(data)}")
print(f"NaN count: {np.isnan(data).sum()}")
print(f"Inf count: {np.isinf(data).sum()}")

# Safe RMS calculation
finite_data = data[np.isfinite(data)]
if len(finite_data) > 0:
    rms = np.sqrt(np.mean(finite_data**2))
    print(f"RMS (finite only): {rms:.8f}")
    if rms < 0.0001:
        print("\n*** VERY LOW AUDIO - Stereo Mix is likely NOT capturing system audio ***")
        print("*** Check: Windows Sound Settings > Recording > Stereo Mix > Properties > Levels ***")
    elif rms < 0.01:
        print("\n*** Low audio level but detectable ***")
    else:
        print(f"\n*** Good audio level! ***")
else:
    print("ALL data is NaN/Inf!")

# Show first 20 samples
print(f"\nFirst 20 samples: {data[:20]}")
print(f"Middle 20 samples: {data[len(data)//2:len(data)//2+20]}")

# Also try with int16 format
print(f"\n--- Testing with int16 format ---")
recording2 = sd.rec(int(1.0 * SAMPLERATE), 
                    samplerate=SAMPLERATE, 
                    channels=CHANNELS, 
                    device=DEVICE_INDEX,
                    dtype='int16')
sd.wait()
data2 = recording2.flatten().astype(np.float32) / 32768.0
rms2 = np.sqrt(np.mean(data2**2))
print(f"int16 RMS: {rms2:.8f}")
print(f"int16 non-zero: {np.count_nonzero(data2)} / {len(data2)}")
print(f"int16 first 20 samples: {recording2.flatten()[:20]}")
