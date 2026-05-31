import customtkinter as ctk
import threading
from audio import get_audio_devices, find_default_microphone_device, find_system_audio_device

class SettingsPage(ctk.CTkFrame):
    """
    Dedicated Settings page showing AI APIs, Audio Hardware, and VAD Sensitivity.
    Arranged in a grid of cards to avoid scrolling and ensure absolute ease-of-use.
    """
    def __init__(self, parent, config_manager, recorder, analyzer, restart_recording_callback, **kwargs):
        super().__init__(parent, fg_color="#121214", **kwargs)
        self.config_manager = config_manager
        self.recorder = recorder
        self.analyzer = analyzer
        self.restart_recording_callback = restart_recording_callback
        
        # Audio device lists
        self.filtered_devices = []
        self.devices = []
        
        # Split layout: 2 equal columns, 2 rows
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_ui()
        
    def _build_ui(self):
        # CARD 1: AI API CONFIGURATION (Row 0, Col 0)
        self.ai_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        self.ai_card.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.ai_card.grid_columnconfigure(0, weight=1)
        
        ai_title = ctk.CTkLabel(self.ai_card, text="การตั้งค่าระบบปัญญาประดิษฐ์ (AI API Settings)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF")
        ai_title.pack(anchor="w", padx=20, pady=(20, 5))
        
        ai_desc = ctk.CTkLabel(self.ai_card, text="เชื่อมต่อกับโมเดล Gemini เพื่อทำการวิเคราะห์โครงสร้างและสรุปแนวคำตอบสัมภาษณ์", font=ctk.CTkFont(size=11), text_color="#888888", justify="left")
        ai_desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        # API Key Field
        key_lbl = ctk.CTkLabel(self.ai_card, text="คีย์เปิดใช้งาน Gemini API Key:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        key_lbl.pack(anchor="w", padx=20, pady=(5, 2))
        
        self.api_key_entry = ctk.CTkEntry(
            self.ai_card,
            placeholder_text="วางคีย์ AIzaSy... ของคุณที่นี่",
            show="*",
            height=32
        )
        self.api_key_entry.insert(0, self.config_manager.get("gemini_api_key", ""))
        self.api_key_entry.pack(fill="x", padx=20, pady=(2, 8))
        self.api_key_entry.bind("<FocusOut>", self._save_api_key)
        
        # API Key Action Frame
        key_actions = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        key_actions.pack(fill="x", padx=20, pady=(2, 12))
        
        self.test_key_btn = ctk.CTkButton(
            key_actions,
            text=" ทดสอบเชื่อมต่อ",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=110,
            height=28,
            fg_color="#2B2B30",
            hover_color="#3A3A40",
            command=self._on_test_api_key
        )
        self.test_key_btn.pack(side="left")
        
        self.key_status_lbl = ctk.CTkLabel(
            key_actions,
            text="ยังไม่ได้ทดสอบเชื่อมต่อ",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.key_status_lbl.pack(side="left", padx=10)
        
        # Model Selection dropdown
        model_lbl = ctk.CTkLabel(self.ai_card, text="โมเดลปัญญาประดิษฐ์ (Gemini Model):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        model_lbl.pack(anchor="w", padx=20, pady=(10, 2))
        
        self.model_menu = ctk.CTkOptionMenu(
            self.ai_card,
            values=["gemini-3.1-flash-lite", "gemini-flash-lite-latest"],
            height=32,
            command=self._on_model_changed
        )
        saved_model = self.config_manager.get("gemini_model", "gemini-3.1-flash-lite")
        self.model_menu.set(saved_model)
        self.model_menu.pack(fill="x", padx=20, pady=(2, 10))

        # CARD 2: AUDIO HARDWARE (Row 0, Col 1)
        self.audio_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        self.audio_card.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        self.audio_card.grid_columnconfigure(0, weight=1)
        
        audio_title = ctk.CTkLabel(self.audio_card, text="ระบบเสียงและฮาร์ดแวร์ (Audio Hardware)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF")
        audio_title.pack(anchor="w", padx=20, pady=(20, 5))
        
        audio_desc = ctk.CTkLabel(self.audio_card, text="เลือกต้นทางสัญญาณเสียงที่คุณต้องการบันทึกและตัดเสียงรบกวน", font=ctk.CTkFont(size=11), text_color="#888888", justify="left")
        audio_desc.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Source switch segment button
        source_lbl = ctk.CTkLabel(self.audio_card, text="เลือกประเภทการดักจับ (Audio Source):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        source_lbl.pack(anchor="w", padx=20, pady=(5, 2))
        
        self.source_switch = ctk.CTkSegmentedButton(
            self.audio_card,
            values=["ไมโครโฟน", "เสียงระบบ/ลำโพง"],
            height=32,
            command=self._on_source_type_changed
        )
        saved_source = self.config_manager.get("audio_source_type", "mic")
        self.source_switch.set("ไมโครโฟน" if saved_source == "mic" else "เสียงระบบ/ลำโพง")
        self.source_switch.pack(fill="x", padx=20, pady=(2, 10))
        
        # Device list menu
        self.device_label = ctk.CTkLabel(self.audio_card, text="เลือกอุปกรณ์นำเข้าเสียง (Input Device):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        self.device_label.pack(anchor="w", padx=20, pady=(8, 2))
        
        self.device_menu = ctk.CTkOptionMenu(
            self.audio_card,
            values=["กำลังดึงรายชื่ออุปกรณ์เสียง..."],
            height=32,
            command=self._on_device_changed
        )
        self.device_menu.pack(fill="x", padx=20, pady=(2, 12))
        self._update_device_dropdown()
        
        # Noise reduction switch
        self.noise_red_switch = ctk.CTkSwitch(
            self.audio_card,
            text="เปิดระบบลดเสียงรบกวนเชิงคณิตศาสตร์ (Noise Reduction)",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_noise_reduction_changed
        )
        saved_noise_red = self.config_manager.get("noise_reduction_enabled", True)
        if saved_noise_red:
            self.noise_red_switch.select()
        else:
            self.noise_red_switch.deselect()
        self.noise_red_switch.pack(anchor="w", padx=20, pady=(10, 10))

        # CARD 3: SENSITIVITY & VAD SETTINGS (Row 1, Column 0 & 1 merged/spanned)
        self.vad_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        self.vad_card.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")
        self.vad_card.grid_columnconfigure(0, weight=1)
        self.vad_card.grid_columnconfigure(1, weight=1)
        
        vad_title = ctk.CTkLabel(self.vad_card, text="ระบบคัดกรองเสียงอัจฉริยะ (VAD & Sensitivity)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF")
        vad_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 5))
        
        vad_desc = ctk.CTkLabel(
            self.vad_card, 
            text="ปรับแต่งช่วงความกว้างระดับเกณฑ์เสียงพูด เพื่อให้ระบบวิเคราะห์คำเสียงพูดอัตโนมัติได้อย่างรวดเร็วและเป็นธรรมชาติ", 
            font=ctk.CTkFont(size=11), 
            text_color="#888888", 
            justify="left"
        )
        vad_desc.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 20))
        
        # Left Slider: VAD Threshold (Sensitivity)
        threshold_val = self.config_manager.get("silence_threshold", 0.015)
        self.threshold_label = ctk.CTkLabel(
            self.vad_card, 
            text=f"เกณฑ์ระดับเสียงพูดขั้นต่ำ (Sensitivity): {threshold_val:.3f}", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#BBBBBB"
        )
        self.threshold_label.grid(row=2, column=0, sticky="w", padx=20, pady=(5, 2))
        
        self.threshold_slider = ctk.CTkSlider(
            self.vad_card,
            from_=0.001,
            to=0.300,
            number_of_steps=150,
            command=self._on_threshold_changed
        )
        self.threshold_slider.set(threshold_val)
        self.threshold_slider.grid(row=3, column=0, padx=20, pady=(2, 15), sticky="ew")
        
        # Right Slider: Silence Duration
        duration_val = self.config_manager.get("silence_duration", 1.2)
        self.duration_label = ctk.CTkLabel(
            self.vad_card, 
            text=f"เวลารอกดจบคำถามเมื่อหยุดพูด (Silence Duration): {duration_val:.2f} วินาที", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#BBBBBB"
        )
        self.duration_label.grid(row=2, column=1, sticky="w", padx=20, pady=(5, 2))
        
        self.duration_slider = ctk.CTkSlider(
            self.vad_card,
            from_=0.50,
            to=4.00,
            number_of_steps=70,
            command=self._on_duration_changed
        )
        self.duration_slider.set(duration_val)
        self.duration_slider.grid(row=3, column=1, padx=20, pady=(2, 15), sticky="ew")
        
    # =====================================================================
    # EVENT HANDLERS
    # =====================================================================
    
    def _save_api_key(self, event=None):
        api_key = self.api_key_entry.get().strip()
        self.config_manager.set("gemini_api_key", api_key)
        self.analyzer.update_api_key(api_key)
        print("[Settings Log] Gemini API Key updated and saved.")

    def _on_test_api_key(self):
        # Save key first to ensure config and analyzer have it
        self._save_api_key()
        
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.key_status_lbl.configure(text="กรุณากรอก API Key ก่อนทดสอบ", text_color="#D9534F")
            return
            
        self.key_status_lbl.configure(text="กำลังทดสอบเชื่อมต่อ...", text_color="#3498DB")
        self.test_key_btn.configure(state="disabled")
        
        def run_test():
            success, msg = self.analyzer.validate_api_key()
            self.after(0, lambda: self._update_test_status(success, msg))
            
        threading.Thread(target=run_test, daemon=True).start()

    def _update_test_status(self, success, msg):
        self.test_key_btn.configure(state="normal")
        if success:
            self.key_status_lbl.configure(text=msg, text_color="#2ECC71")
        else:
            self.key_status_lbl.configure(text=msg, text_color="#D9534F")
        
    def _on_model_changed(self, selected_model):
        self.config_manager.set("gemini_model", selected_model)
        self.analyzer.update_model_name(selected_model)
        print(f"[Settings Log] Gemini Model changed to {selected_model}")
        
    def _on_source_type_changed(self, source_type_thai):
        source_type = "mic" if source_type_thai == "ไมโครโฟน" else "system"
        self.config_manager.set("audio_source_type", source_type)
        self.recorder.source_type = source_type
        print(f"[Settings Log] Audio source changed to {source_type}")
        
        # Re-populate input device list
        self._update_device_dropdown()
        
        # Trigger immediate restart to apply settings
        self.restart_recording_callback()
        
    def _on_device_changed(self, selected_desc):
        device_index = None
        for d in self.filtered_devices:
            if d["desc"] == selected_desc:
                device_index = d["index"]
                break
                
        if device_index is not None:
            self.config_manager.set("audio_device_index", device_index)
            self.recorder.device_index = device_index
            print(f"[Settings Log] Input device changed to index {device_index} ({selected_desc})")
            
            # Restart to capture on the new device index
            self.restart_recording_callback()
            
    def _on_noise_reduction_changed(self):
        val = bool(self.noise_red_switch.get())
        self.config_manager.set("noise_reduction_enabled", val)
        self.recorder.noise_reduction_enabled = val
        print(f"[Settings Log] Noise reduction toggled to {val}")
        
    def _on_threshold_changed(self, value):
        val = round(float(value), 3)
        self.threshold_label.configure(text=f"เกณฑ์ระดับเสียงพูดขั้นต่ำ (Sensitivity): {val:.3f}")
        self.config_manager.set("silence_threshold", val)
        self.recorder.silence_threshold = val
        
    def _on_duration_changed(self, value):
        val = round(float(value), 2)
        self.duration_label.configure(text=f"เวลารอกดจบคำถามเมื่อหยุดพูด (Silence Duration): {val:.2f} วินาที")
        self.config_manager.set("silence_duration", val)
        self.recorder.silence_duration = val
        
    # =====================================================================
    # PUBLIC HARDWARE SYNC HELPERS (Called from app.py)
    # =====================================================================
    
    def on_calibration_complete(self, tuned_threshold):
        """Sync auto-calibrated threshold to slider and config."""
        self.threshold_slider.set(tuned_threshold)
        self.threshold_label.configure(text=f"เกณฑ์ระดับเสียงพูดขั้นต่ำ (Sensitivity): {tuned_threshold:.3f}")
        
    def on_device_auto_switched(self, new_device_index):
        """Called if hardware switches index automatically."""
        self.config_manager.set("audio_device_index", new_device_index)
        for d in self.filtered_devices:
            if d["index"] == new_device_index:
                self.device_menu.set(d["desc"])
                return
        self._update_device_dropdown()
        
    def _update_device_dropdown(self):
        source_type = self.config_manager.get("audio_source_type", "mic")
        self.devices = get_audio_devices()
        
        filtered = []
        for d in self.devices:
            name_lower = d["name"].lower()
            if source_type == "mic":
                if not d["is_loopback"] and "stereo mix" not in name_lower:
                    filtered.append(d)
            else:
                if d["is_loopback"] or "stereo mix" in name_lower:
                    filtered.append(d)
                    
        # Sort in case of system loopback devices
        if source_type != "mic" and filtered:
            def _sort_key(d):
                if "stereo mix" in d["name"].lower():
                    return 0
                elif not d.get("is_pure_loopback", False):
                    return 1
                else:
                    return 2
            filtered.sort(key=_sort_key)
            
        self.filtered_devices = filtered
        names = [d["desc"] for d in filtered] if filtered else ["ไม่พบไดรเวอร์เสียงในระบบ"]
        self.device_menu.configure(values=names)
        
        if source_type == "mic":
            self.device_label.configure(text="เลือกไมโครโฟนของคุณ (Microphone Device):")
        else:
            self.device_label.configure(text="เลือกอุปกรณ์เสียงระบบ (Speakers/Stereo Mix):")
            
        saved_index = self.config_manager.get("audio_device_index")
        selected_desc = None
        for d in filtered:
            if d["index"] == saved_index:
                selected_desc = d["desc"]
                break
                
        if not selected_desc and filtered:
            if source_type == "mic":
                idx = find_default_microphone_device()
            else:
                idx = find_system_audio_device()
                
            for d in filtered:
                if d["index"] == idx:
                    selected_desc = d["desc"]
                    saved_index = idx
                    break
            if not selected_desc:
                selected_desc = filtered[0]["desc"]
                saved_index = filtered[0]["index"]
                
        if selected_desc:
            self.device_menu.set(selected_desc)
            self.config_manager.set("audio_device_index", saved_index)
            self.recorder.device_index = saved_index
        else:
            self.device_menu.set("กรุณาเลือกอุปกรณ์เสียง")
