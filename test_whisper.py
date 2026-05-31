import sys
import time
import numpy as np
import sounddevice as sd
from transcriber import WhisperTranscriber
from audio import resample_audio

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def test_whisper():
    print("--- TESTING LOCAL WHISPER TRANSCRIPTION ---")
    
    # Initialize transcriber with 'tiny' model for fast verification
    transcriber = WhisperTranscriber(model_size="tiny", device="cpu", compute_type="int8")
    
    import threading
    event = threading.Event()
    
    def on_loaded(success, message):
        print(f"Whisper Model Load Callback: Success={success}, Message={message}")
        event.set()
        
    transcriber.start_loading(on_complete=on_loaded)
    
    print("Waiting for model to download and load...")
    event.wait()
    
    if not transcriber.is_loaded:
        print("Whisper failed to load. Aborting.")
        return
        
    print("\n--- RECORDING TEST PHRASE (3 seconds) ---")
    print("Please say something (e.g., 'Hello, test' or 'สวัสดีครับ') in 3... 2... 1...")
    
    samplerate = 44100
    duration = 3.0
    try:
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        print("Recording complete. Resampling and transcribing...")
        
        # Prepare audio
        audio_mono = audio.flatten()
        resampled = resample_audio(audio_mono, samplerate, 16000)
        
        # Transcribe directly using the loaded model
        segments, info = transcriber.model.transcribe(resampled, beam_size=5)
        text = " ".join([seg.text for seg in segments]).strip()
        
        print("\n--- TRANSCRIPTION RESULT ---")
        print(f"Detected Language: {info.language} (confidence: {info.language_probability:.2f})")
        print(f"Text: '{text}'")
        print("----------------------------")
        print("Whisper offline test PASSED!")
        
    except Exception as e:
        print(f"Error during recording/transcribing: {e}")

if __name__ == "__main__":
    test_whisper()
