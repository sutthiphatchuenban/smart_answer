from audio import get_audio_devices, find_system_audio_device, find_default_microphone_device

devs = get_audio_devices()
print(f"\n{'='*80}")
print(f"Found {len(devs)} audio devices:")
print(f"{'='*80}")
for d in devs:
    flags = []
    if d.get("is_loopback"):
        flags.append("LOOPBACK")
    if d.get("is_pure_loopback"):
        flags.append("PURE_LOOPBACK(UNUSABLE)")
    if "stereo mix" in d["name"].lower():
        flags.append("STEREO_MIX(RECOMMENDED)")
    flag_str = f" [{', '.join(flags)}]" if flags else ""
    print(f"  idx={d['index']:2d}  ch={d['channels']}  rate={d['default_samplerate']:5d}  | {d['desc']}{flag_str}")

print(f"\n--- Auto-detection results ---")
sys_idx = find_system_audio_device()
mic_idx = find_default_microphone_device()
print(f"  Best system audio device: index={sys_idx}")
print(f"  Best microphone device:   index={mic_idx}")

# Quick test: try opening Stereo Mix
print(f"\n--- Testing Stereo Mix capture ---")
for d in devs:
    if "stereo mix" in d["name"].lower():
        import sounddevice as sd
        import numpy as np
        try:
            print(f"  Testing device {d['index']}: {d['desc']}...")
            duration = 2.0  # Record 2 seconds
            recording_raw = sd.rec(int(duration * d['default_samplerate']), 
                             samplerate=d['default_samplerate'], 
                             channels=1, 
                             device=d['index'],
                             dtype='int16')
            sd.wait()
            recording = recording_raw.astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(recording**2))
            max_val = np.max(np.abs(recording))
            print(f"  SUCCESS! Recorded {len(recording)} samples. RMS={rms:.6f}, Max={max_val:.6f}")
            if rms < 0.001:
                print(f"  WARNING: Very low audio level! Stereo Mix volume may be too low in Windows Sound settings.")
            else:
                print(f"  Audio level looks good!")
        except Exception as e:
            print(f"  FAILED: {e}")
        break
else:
    print("  No Stereo Mix device found!")
