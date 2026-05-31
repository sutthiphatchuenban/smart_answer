import os
import sys
import queue
import threading
import time
import customtkinter as ctk
from tkinter import messagebox

# Reconfigure stdout/stderr to handle encoding errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Import core modules
from config import ConfigManager
from audio import AudioRecorder
from transcriber import WhisperTranscriber  # Backed by Google Speech Recognition
from gemini_client import GeminiAnalyzer

# Import UI components
from ui import NavigationFrame, DashboardPage, HistoryPage, SettingsPage, create_coaching_card

# Set appearance settings for customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SmartAnswerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Smart Answer - Interview Prep Assistant")
        self.geometry("1150x800")
        self.minsize(1000, 700)
        
        # Set custom window and taskbar icon
        try:
            # Set AppUserModelID to force Windows to display our custom taskbar icon
            import ctypes
            myappid = 'smartanswer.interviewassistant.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"[Icon Log] Failed to set AppUserModelID: {e}")

        try:
            from ui.svg_images import get_svg_image, SVG_BRAIN
            from PIL import ImageTk
            icon_img = get_svg_image(SVG_BRAIN, size=(64, 64))._light_image
            icon_photo = ImageTk.PhotoImage(icon_img)
            self._icon_ref = icon_photo  # Keep a reference to prevent garbage collection
            self.iconphoto(False, icon_photo)
        except Exception as e:
            print(f"[Icon Log] Failed to set window icon: {e}")
        
        # Initialize Managers
        self.config_manager = ConfigManager()
        self.recorder = AudioRecorder(
            device_index=self.config_manager.get("audio_device_index"),
            silence_threshold=self.config_manager.get("silence_threshold", 0.015),
            silence_duration=self.config_manager.get("silence_duration", 1.2),
            noise_reduction_enabled=self.config_manager.get("noise_reduction_enabled", True),
            source_type=self.config_manager.get("audio_source_type", "mic")
        )
        self.transcriber = WhisperTranscriber(
            model_size=self.config_manager.get("whisper_model", "base"),
            compute_type=self.config_manager.get("compute_type", "int8")
        )
        self.analyzer = GeminiAnalyzer(
            api_key=self.config_manager.get("gemini_api_key"),
            model_name=self.config_manager.get("gemini_model", "gemini-3.1-flash-lite"),
            provider=self.config_manager.get("ai_provider", "gemini"),
            custom_api_key=self.config_manager.get("custom_api_key", ""),
            custom_base_url=self.config_manager.get("custom_base_url", ""),
            custom_model=self.config_manager.get("custom_model", "")
        )
        
        # App-level state
        self.is_recording = False
        self.is_speaking = False
        self.pulse_state = False
        self.last_live_caption_update = 0.0
        self.last_live_caption_text = ""
        self.last_status_desc = ""
        self.is_mini_mode = False
        self.normal_geometry = "1150x800"
        
        # State for scrollable feed
        self.session_results = []  # Stores results of the current session
        self.coaching_cards = []   # Keeps references to widget cards in the feed
        self.viewing_history = False
        
        # Build UI layout
        self._build_ui()
        
        # Set up recorder callbacks (bridging page elements + main content)
        self.recorder.live_audio_callback = self._on_live_audio_received
        self.recorder.calibration_callback = self._on_calibration_complete
        self.recorder.device_switch_callback = self._on_device_auto_switched
        self.recorder.speech_status_callback = self._on_speech_status_changed
        
        # Start background threads
        self._init_backend()
        
        # Load saved history into history page
        self._load_saved_history()
        
        # If API Key is empty, automatically redirect the user to Settings page
        if not self.config_manager.get("gemini_api_key"):
            self.after(500, lambda: self._switch_page("settings"))
            self.after(500, lambda: self.navigation.select_page("settings"))
        
    def _safe_gui_update(self, func, *args, **kwargs):
        """Helper to run GUI updates on the main thread safely."""
        self.after(0, lambda: func(*args, **kwargs))

    def _set_status_desc(self, text):
        if text == self.last_status_desc:
            return
        self.last_status_desc = text
        self.main_content.status_desc.configure(text=text)
        self.navigation.status_desc.configure(text=text)

    def _init_backend(self):
        # Bind transcriber
        self.transcriber.start_processing(
            audio_queue=self.recorder.audio_queue,
            transcription_callback=self._on_question_transcribed,
            status_callback=self._on_transcriber_status_change
        )
        
        # Load speech backend in background
        self.transcriber.start_loading(on_complete=self._on_whisper_loaded)

    def _build_ui(self):
        # Grid layout (1 row, 2 columns: Left Navigation Menu & Right Page Container)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Navigation Menu
        self.grid_columnconfigure(1, weight=1) # Page Container
        
        # LEFT NAVIGATION MENU
        self.navigation = NavigationFrame(
            self,
            switch_page_callback=self._switch_page
        )
        self.navigation.grid(row=0, column=0, sticky="nsew")
        
        # RIGHT PAGE CONTAINER
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Pages setup
        self.dashboard_page = DashboardPage(
            self.container,
            recorder=self.recorder,
            callbacks={
                'toggle_recording': self._toggle_recording,
                'toggle_mini_mode': self._toggle_mini_mode
            }
        )
        self.dashboard_page.grid(row=0, column=0, sticky="nsew")
        
        self.history_page = HistoryPage(
            self.container,
            config_manager=self.config_manager
        )
        self.history_page.grid(row=0, column=0, sticky="nsew")
        
        self.settings_page = SettingsPage(
            self.container,
            config_manager=self.config_manager,
            recorder=self.recorder,
            analyzer=self.analyzer,
            restart_recording_callback=self._restart_recording_from_settings
        )
        self.settings_page.grid(row=0, column=0, sticky="nsew")
        
        # Page dictionary for switching
        self.pages = {
            'dashboard': self.dashboard_page,
            'history': self.history_page,
            'settings': self.settings_page
        }
        
        # Map main_content to dashboard_page to keep callbacks backward-compatible
        self.main_content = self.dashboard_page
        
        # Set default active page
        self._switch_page('dashboard')

    def _switch_page(self, page_name):
        # Hide all pages and show the requested one
        for name, page in self.pages.items():
            if name == page_name:
                page.grid()
                page.tkraise()
            else:
                page.grid_remove()

    def _toggle_mini_mode(self):
        self.is_mini_mode = not self.is_mini_mode
        if self.is_mini_mode:
            # Switch to Dashboard first to ensure correct view
            self._switch_page('dashboard')
            
            # Save normal geometry and size
            self.normal_geometry = self.geometry()
            
            # Hide sidebar navigation frame
            self.navigation.grid_remove()
            
            # Put dashboard in mini layout
            self.dashboard_page.set_mini_mode(True)
            
            # Change window settings
            self.resizable(False, False) # Disable resizing during mini mode
            self.geometry("470x200") # Set small size
            self.attributes("-topmost", True) # Floating topmost
        else:
            # Restore window settings
            self.attributes("-topmost", False)
            self.resizable(True, True)
            
            # Put dashboard back to normal layout
            self.dashboard_page.set_mini_mode(False)
            
            # Restore sidebar navigation frame
            self.navigation.grid()
            
            # Restore normal size
            self.geometry(self.normal_geometry)

    def _restart_recording_from_settings(self):
        if self.is_recording:
            self._toggle_recording()
            self._toggle_recording()

    # =====================================================================
    # RECORDING CONTROL
    # =====================================================================

    def _toggle_recording(self):
        if not self.transcriber.is_loaded:
            messagebox.showwarning("กำลังโหลดตัวจับเสียง", "กรุณารอระบบถอดความเชื่อมต่อเสร็จสิ้นสักครู่...")
            return
            
        if not self.is_recording:
            # Start Recording
            mode = "manual" if self.dashboard_page.mode_switch.get() == "Manual Mode" else "auto"
            self.recorder.start(mode=mode)
            self.is_recording = True
            
            # Update dashboard controls
            self.dashboard_page.set_recording_state(True)
            self.dashboard_page.update_record_button(True, mode)
            
            # Update status
            self.main_content.status_title.configure(
                text="กำลังวัดระดับเสียงรบกวน..." if mode == "manual" else "กำลังวัดเสียงรบกวน..."
            )
            self.main_content.status_dot.configure(text_color="#f0ad4e")  # Orange during calibration
            self.main_content.status_desc.configure(
                text="กรุณาเงียบเสียง 1.2 วินาที เพื่อสร้างโปรไฟล์การตัดเสียงรบกวนและระดับ VAD..."
            )
            self.navigation.set_status("กำลังคำนวณระดับเสียง...", "#f0ad4e", "กรุณาเงียบเสียงสักครู่...")
            
            # Start Pulsing Animation
            self.pulse_state = True
            self._pulse_recording_indicator()
        else:
            # Stop Recording
            self.recorder.stop()
            self.is_recording = False
            self.pulse_state = False
            
            # Update dashboard controls
            self.dashboard_page.set_recording_state(False)
            self.dashboard_page.update_record_button(False)
            
            # Update status
            self.main_content.status_title.configure(text="Ready to capture")
            self.main_content.status_dot.configure(text_color="#28a745")  # Green for standby
            self.main_content.status_desc.configure(text="กดปุ่ม 'Start Listening' หรือเลือกเป็น Auto-Trigger เพื่อเริ่มจับสัญญาณเสียงอัตโนมัติ")
            self.navigation.set_status("พร้อมใช้งาน", "#28a745", "พร้อมเริ่มดักจับสัญญาณเสียง")

    def _pulse_recording_indicator(self):
        """Pulsing dot micro-animation for recording indicator."""
        if not self.is_recording:
            return
            
        if self.pulse_state:
            # If calibration completed, we show red, else keep flashing orange
            if not self.recorder.calibrating:
                if not self.is_speaking:
                    mode_title = "พร้อมพูดได้เลย! (ระบบสแตนด์บายจับเสียงอัตโนมัติ VAD)" if self.dashboard_page.mode_switch.get() == "Auto-Trigger" else "พร้อมพูดได้เลย! (กำลังดักจับสัญญาณเสียง)"
                    self.main_content.status_title.configure(text=mode_title)
                    self.navigation.set_status("พร้อมพูดได้เลย", self.main_content.status_dot.cget("text_color"), "ระบบสแตนด์บายดักฟังเสียงแล้ว")
                
                current_color = self.main_content.status_dot.cget("text_color")
                next_color = "#800000" if current_color == "#d9534f" else "#d9534f"
                self.main_content.status_dot.configure(text_color=next_color)
            else:
                current_color = self.main_content.status_dot.cget("text_color")
                next_color = "#a37027" if current_color == "#f0ad4e" else "#f0ad4e"
                self.main_content.status_dot.configure(text_color=next_color)
                self.navigation.set_status("กำลังวัดระดับเสียง...", next_color, "กรุณาเงียบเสียงสักครู่...")
            
        self.after(600, self._pulse_recording_indicator)

    # =====================================================================
    # RECORDER CALLBACKS
    # =====================================================================

    def _on_speech_status_changed(self, is_speaking):
        """Called from recorder thread when VAD speech begins or ends."""
        def update():
            if not self.is_recording:
                return
            self.is_speaking = is_speaking
            if is_speaking:
                self.main_content.status_title.configure(text="กำลังดักฟังเสียงพูดของคุณ... (กำลังบันทึกเสียง)")
                self.main_content.status_dot.configure(text_color="#d9534f")  # Steady red
                self.navigation.set_status("กำลังพูด...", "#d9534f", "กำลังดักจับและสะสมสัญญาณเสียง")
            else:
                mode_title = "พร้อมพูดได้เลย! (ระบบสแตนด์บายจับเสียงอัตโนมัติ VAD)" if self.dashboard_page.mode_switch.get() == "Auto-Trigger" else "พร้อมพูดได้เลย! (กำลังดักจับสัญญาณเสียง)"
                self.main_content.status_title.configure(text=mode_title)
                self.navigation.set_status("พร้อมพูดได้เลย", "#d9534f", "ระบบสแตนด์บายดักฟังเสียงแล้ว")
        self._safe_gui_update(update)

    def _on_calibration_complete(self, tuned_threshold):
        def update():
            self.settings_page.on_calibration_complete(tuned_threshold)
            self.main_content.status_desc.configure(text="วัดระดับเสียงรบกวนรอบตัวสำเร็จ! เริ่มพูดถามคำถามได้ทันที")
            self.navigation.set_status("พร้อมพูดได้เลย", "#d9534f", "วัดเสียงรบกวนรอบตัวสำเร็จแล้ว")
        self._safe_gui_update(update)

    def _on_device_auto_switched(self, new_device_index):
        """Called from recorder thread when device is auto-switched. Updates UI dropdown."""
        def update():
            self.settings_page.on_device_auto_switched(new_device_index)
        self._safe_gui_update(update)

    # =====================================================================
    # TRANSCRIPTION & ANALYSIS CALLBACKS
    # =====================================================================

    def _on_whisper_loaded(self, success, message):
        if success:
            self._safe_gui_update(self.main_content.status_title.configure, text="ตัวจับเสียง Google Speech พร้อมใช้งาน")
            self._safe_gui_update(self.main_content.status_dot.configure, text_color="#28a745")  # Green
            self._safe_gui_update(self.main_content.status_desc.configure, text="สแตนด์บายพร้อมใช้งาน กดปุ่ม 'Start Listening' เพื่อเริ่มดักจับเสียง")
            self._safe_gui_update(self.navigation.set_status, "พร้อมใช้งาน", "#28a745", "Google Speech API เชื่อมต่อสำเร็จ")
        else:
            self._safe_gui_update(self.main_content.status_title.configure, text="เชื่อมต่อตัวจับเสียงล้มเหลว")
            self._safe_gui_update(self.main_content.status_dot.configure, text_color="#dc3545")  # Red
            self._safe_gui_update(self.main_content.status_desc.configure, text=f"Google Speech Initializer Error: {message}")
            self._safe_gui_update(self.navigation.set_status, "เชื่อมต่อล้มเหลว", "#dc3545", f"Error: {message}")

    def _on_transcriber_status_change(self, status):
        self._safe_gui_update(self._set_status_desc, status)
        if "แปลงเสียงเป็นข้อความ" in status:
            self._safe_gui_update(self.main_content.status_title.configure, text="กำลังประมวลผล... (พูดประโยคต่อไปได้ทันที)")
            self._safe_gui_update(self.main_content.status_dot.configure, text_color="#f0ad4e")  # Orange
            self._safe_gui_update(self.navigation.set_status, "กำลังถอดความ...", "#f0ad4e", status)
        elif "พร้อมใช้งาน" in status or "Ready" in status:
            if self.is_recording:
                mode_desc = "กำลังสแตนด์บายจับเสียงอัตโนมัติ (VAD)..." if self.dashboard_page.mode_switch.get() == "Auto-Trigger" else "กำลังดักจับสัญญาณเสียง..."
                self._safe_gui_update(self.main_content.status_title.configure, text=mode_desc)
                self._safe_gui_update(self.main_content.status_dot.configure, text_color="#d9534f")  # Red
                self._safe_gui_update(self.navigation.set_status, "กำลังดักจับเสียง...", "#d9534f", mode_desc)

    def _on_live_audio_received(self, audio_data):
        self.transcriber.transcribe_live(audio_data, self._on_live_transcription_received)

    def _on_live_transcription_received(self, text, lang):
        def update_live():
            if self.is_recording:
                now = time.time()
                live_text = f"{text} (ภาษา: {lang})"
                if live_text == self.last_live_caption_text:
                    return
                if now - self.last_live_caption_update < 0.75:
                    return
                self.last_live_caption_update = now
                self.last_live_caption_text = live_text
                self.main_content.update_live_caption(live_text)
        self._safe_gui_update(update_live)

    def _on_question_transcribed(self, text, lang):
        print(f"Final Transcribed Text: {text} ({lang})")
        
        # Display final text in live caption box
        def update_live_final():
            self.main_content.update_live_caption(f'ประโยคล่าสุด: "{text}"')
        self._safe_gui_update(update_live_final)
        
        # Trigger Gemini Analysis
        self.analyzer.analyze_question(
            question_text=text,
            callback=self._on_analysis_received,
            status_callback=lambda s: self._safe_gui_update(self.main_content.status_desc.configure, text=s)
        )

    def _on_analysis_received(self, result, error):
        if error:
            self._safe_gui_update(messagebox.showerror, "Gemini Error", error)
            self._safe_gui_update(self.main_content.status_title.configure, text="Gemini Error")
            self._safe_gui_update(self.main_content.status_dot.configure, text_color="#dc3545")
            self._safe_gui_update(self.main_content.status_desc.configure, text=error)
            return

        if not result:
            return

        # Check if the text was actually recognized as an interview question by Gemini
        is_q = result.get("is_interview_question", True)
        if not is_q:
            print("Gemini flagged the text as casual chit-chat (not an interview question). Ignoring.")
            self._safe_gui_update(self.main_content.status_desc.configure, text="ข้ามข้อความพูดคุยทั่วไป (ไม่เพิ่มใน Feed)")
            return

        # Add to history
        q_text = result.get("question_thai") or "คำถามสัมภาษณ์"
        
        def process_update():
            # In Dashboard mode, we don't have to back-banner because history has its own page!
            if self.session_results:
                last_q = self.session_results[-1].get("question_thai")
                if last_q == q_text:
                    print(f"[App Log] Duplicate consecutive question '{q_text}' detected. Replacing last card.")
                    if self.coaching_cards:
                        last_card = self.coaching_cards.pop()
                        last_card.destroy()
                    self.session_results.pop()
            
            self.config_manager.add_to_history(q_text, result)
            self._load_saved_history()
            self._add_result_to_session_and_feed(result)
            
        self._safe_gui_update(process_update)

    # =====================================================================
    # FEED MANAGEMENT
    # =====================================================================

    def _add_result_to_session_and_feed(self, result):
        self._add_coaching_card_to_feed(result, add_to_session=True)

    def _add_coaching_card_to_feed(self, result, add_to_session=True):
        # Remove empty state label if present
        self.main_content.hide_empty_state()

        if add_to_session:
            card_idx = len(self.session_results) + 1
            self.session_results.append(result)
            card_label = f"#{card_idx}"
        else:
            card_label = "History"

        # Build card using the coaching card builder
        card = create_coaching_card(self.main_content.feed_scroll, result, card_label)
        self.coaching_cards.append(card)

        # Auto-scroll feed to bottom
        self.main_content.scroll_feed_to_bottom()

    # =====================================================================
    # HISTORY MANAGEMENT
    # =====================================================================

    def _load_saved_history(self):
        history = self.config_manager.get("history", [])
        self.history_page.load_history(history)

if __name__ == "__main__":
    app = SmartAnswerApp()
    app.mainloop()
