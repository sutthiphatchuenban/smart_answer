import time
import numpy as np
import sounddevice as sd

def test_devices():
    print("--- AUDIO DEVICES LIST ---")
    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        default_in, default_out = sd.default.device
        
        print(f"Default Input Device Index: {default_in}")
        print(f"Default Output Device Index: {default_out}\n")
        
        for i, d in enumerate(devices):
            api = hostapis[d['hostapi']]['name']
            in_ch = d.get('max_input_channels', 0)
            out_ch = d.get('max_output_channels', 0)
            
            prefix = "[DEFAULT IN] " if i == default_in else "[DEFAULT OUT] " if i == default_out else "             "
            
            print(f"{prefix}Index {i}: {d['name']}")
            print(f"              API: {api} | Input Ch: {in_ch} | Output Ch: {out_ch} | Rate: {d['default_samplerate']}Hz")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error querying devices: {e}")
        return
        
    print("\n--- TESTING AUDIO INPUT (3 seconds) ---")
    try:
        duration = 3.0  # seconds
        samplerate = 16000
        channels = 1
        
        print("Recording...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
        
        for elapsed in range(3):
            # Print average audio level (RMS) to show it's capturing
            time.sleep(1.0)
            chunk = audio[int(elapsed * samplerate):int((elapsed + 1) * samplerate)]
            rms = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0
            # Draw a simple ascii meter
            meter_len = int(rms * 100)
            meter = "#" * min(50, meter_len) + "-" * max(0, 50 - meter_len)
            print(f"Sec {elapsed+1} volume RMS: {rms:.4f} |{meter}|")
            
        sd.wait()
        print("Recording completed successfully!")
        print(f"Recorded array size: {audio.shape}")
        
    except Exception as e:
        print(f"Error recording audio: {e}")
        print("Note: If error is due to channel mismatch, check if the default input device supports mono 16kHz.")

if __name__ == "__main__":
    test_devices()
