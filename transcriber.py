import threading
import queue
import time
import io
import numpy as np
import scipy.io.wavfile as wavfile
import speech_recognition as sr
from config import safe_print as print

class WhisperTranscriber:
    """
    Transcriber class that interfaces with Google Speech Recognition API.
    Named 'WhisperTranscriber' for backwards-compatibility with app.py.
    """
    def __init__(self, model_size="base", compute_type="int8", device="cpu"):
        self.is_loading = False
        self.is_loaded = False
        
        self.audio_queue = None
        self.transcription_callback = None  # callback(text, lang)
        self.status_callback = None         # callback(status_text)
        self.running = False
        self.thread = None
        self.recognizer = sr.Recognizer()
        
        # Lock and flag to prevent stacking of live caption transcription threads
        self.live_transcribe_busy = False
        self.live_lock = threading.Lock()
        
        # Adjust recognizer thresholds for better responsiveness
        self.recognizer.dynamic_energy_threshold = False
        
    def start_loading(self, on_complete=None):
        """Pretends to load a model and triggers the completion callback."""
        self.is_loading = True
        if self.status_callback:
            self.status_callback("กำลังเชื่อมต่อ Google Speech API...")
            
        def load_task():
            time.sleep(0.5)
            self.is_loaded = True
            self.is_loading = False
            print("Google Speech API ready.")
            if self.status_callback:
                self.status_callback("Google Speech API Ready")
            if on_complete:
                on_complete(True, "Google Speech API ready.")
                
        threading.Thread(target=load_task, daemon=True).start()

    def start_processing(self, audio_queue, transcription_callback, status_callback=None):
        """Starts the transcription worker thread."""
        self.audio_queue = audio_queue
        self.transcription_callback = transcription_callback
        if status_callback:
            self.status_callback = status_callback
            
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _process_loop(self):
        print("Google Speech transcription processing loop started.")
        while self.running:
            try:
                if self.audio_queue is None:
                    time.sleep(0.1)
                    continue
                    
                try:
                    audio_data = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if self.status_callback:
                    self.status_callback("กำลังแปลงเสียงเป็นข้อความด้วย Google Speech...")
                    
                t0 = time.time()
                transcription, lang = self._transcribe_audio_data(audio_data)
                t1 = time.time()
                
                print(f"Google Speech Transcription took {t1-t0:.2f}s (Lang: {lang}).")
                print(f"Result: {transcription}")
                
                if self.status_callback:
                    self.status_callback("พร้อมใช้งาน")
                    
                if transcription:
                    if self.transcription_callback:
                        self.transcription_callback(transcription, lang)
                else:
                    print("Transcribed text was empty (likely noise/silence).")
                    
            except Exception as e:
                print(f"Error in transcription loop: {e}")
                if self.status_callback:
                    self.status_callback(f"ข้อผิดพลาดในการถอดความ: {str(e)}")
                time.sleep(0.5)

    def _transcribe_audio_data(self, numpy_audio):
        """Converts float32 resampled numpy array into WAV bytes and transcribes via Google Speech."""
        try:
            # 95% peak volume normalization to ensure audio is loud enough for Google Speech
            max_val = np.max(np.abs(numpy_audio))
            if max_val > 0.001:
                numpy_audio = numpy_audio / max_val * 0.95
                
            # numpy_audio is resampled to 16000Hz. Convert float32 [-1.0, 1.0] to int16 PCM
            audio_int16 = (numpy_audio * 32767).astype(np.int16)
            
            wav_io = io.BytesIO()
            wavfile.write(wav_io, 16000, audio_int16)
            wav_bytes = wav_io.getvalue()
            
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio = self.recognizer.record(source)
            
            # 1. Attempt Thai speech recognition
            try:
                text = self.recognizer.recognize_google(audio, language="th-TH")
                if text and text.strip():
                    return text.strip(), "th"
            except sr.UnknownValueError:
                pass
            
            # 2. Attempt English fallback speech recognition
            try:
                text = self.recognizer.recognize_google(audio, language="en-US")
                if text and text.strip():
                    return text.strip(), "en"
            except sr.UnknownValueError:
                pass
                
            return "", "th"
            
        except Exception as e:
            print(f"Error in Google Speech API call: {e}")
            return "", "th"

    def transcribe_live(self, audio_data, callback):
        """Transcribes audio data in real-time in a background thread, skipping if already busy."""
        if not self.is_loaded:
            return
            
        with self.live_lock:
            if self.live_transcribe_busy:
                return
            self.live_transcribe_busy = True
            
        def worker():
            try:
                t0 = time.time()
                text, lang = self._transcribe_audio_data(audio_data)
                t1 = time.time()
                if text:
                    print(f"[Transcriber Log] Live caption transcribed in {t1-t0:.2f}s: '{text}' (Language: {lang})")
                    callback(text, lang)
                else:
                    print(f"[Transcriber Log] Live caption transcription empty/noise (took {t1-t0:.2f}s).")
            finally:
                with self.live_lock:
                    self.live_transcribe_busy = False
                
        threading.Thread(target=worker, daemon=True).start()
