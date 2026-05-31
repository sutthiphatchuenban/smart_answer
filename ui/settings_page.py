import customtkinter as ctk
import threading
import webbrowser
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
        
        ai_desc = ctk.CTkLabel(self.ai_card, text="เชื่อมต่อกับโมเดล Gemini หรือผู้ให้บริการที่รองรับ OpenAI API สำหรับการวิเคราะห์คำถาม", font=ctk.CTkFont(size=11), text_color="#888888", justify="left")
        ai_desc.pack(anchor="w", padx=20, pady=(0, 15))
        
        # AI Provider Selection
        provider_lbl = ctk.CTkLabel(self.ai_card, text="เลือกผู้ให้บริการ (AI Provider):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        provider_lbl.pack(anchor="w", padx=20, pady=(0, 2))
        
        self.provider_switch = ctk.CTkSegmentedButton(
            self.ai_card,
            values=["Google Gemini", "Custom (OpenAI)"],
            height=32,
            command=self._on_provider_changed
        )
        saved_provider = self.config_manager.get("ai_provider", "gemini")
        self.provider_switch.set("Google Gemini" if saved_provider == "gemini" else "Custom (OpenAI)")
        self.provider_switch.pack(fill="x", padx=20, pady=(2, 15))
        
        # Frame for Google Gemini Settings
        self.gemini_frame = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        
        # API Key Field
        key_lbl = ctk.CTkLabel(self.gemini_frame, text="คีย์เปิดใช้งาน Gemini API Key:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        key_lbl.pack(anchor="w", padx=0, pady=(0, 2))
        
        # Link to get Gemini API Key from Google AI Studio
        link_lbl = ctk.CTkLabel(
            self.gemini_frame,
            text="รับ API Key ฟรีได้ที่: https://aistudio.google.com/api-keys",
            font=ctk.CTkFont(size=11, underline=True),
            text_color="#3498DB",
            cursor="hand2"
        )
        link_lbl.pack(anchor="w", padx=0, pady=(0, 6))
        link_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/api-keys"))
        
        self.api_key_entry = ctk.CTkEntry(
            self.gemini_frame,
            placeholder_text="วางคีย์ AIzaSy... ของคุณที่นี่",
            show="*",
            height=32
        )
        self.api_key_entry.insert(0, self.config_manager.get("gemini_api_key", ""))
        self.api_key_entry.pack(fill="x", padx=0, pady=(2, 8))
        self.api_key_entry.bind("<FocusOut>", self._save_settings)
        
        # Model Selection dropdown
        model_lbl = ctk.CTkLabel(self.gemini_frame, text="โมเดลปัญญาประดิษฐ์ (Gemini Model):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        model_lbl.pack(anchor="w", padx=0, pady=(10, 2))
        
        self.model_menu = ctk.CTkOptionMenu(
            self.gemini_frame,
            values=["gemini-3.1-flash-lite", "gemini-flash-lite-latest"],
            height=32,
            command=self._on_model_changed
        )
        saved_model = self.config_manager.get("gemini_model", "gemini-3.1-flash-lite")
        self.model_menu.set(saved_model)
        self.model_menu.pack(fill="x", padx=0, pady=(2, 10))
        
        # Frame for Custom OpenAI-Compatible Settings
        self.custom_frame = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        
        # Base URL Field
        base_url_lbl = ctk.CTkLabel(self.custom_frame, text="API Base URL (Endpoint):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        base_url_lbl.pack(anchor="w", padx=0, pady=(0, 2))
        
        self.custom_base_url_entry = ctk.CTkEntry(
            self.custom_frame,
            placeholder_text="เช่น https://api.openai.com/v1 หรือ http://localhost:11434/v1",
            height=32
        )
        self.custom_base_url_entry.insert(0, self.config_manager.get("custom_base_url", ""))
        self.custom_base_url_entry.pack(fill="x", padx=0, pady=(2, 8))
        self.custom_base_url_entry.bind("<FocusOut>", self._save_settings)
        
        # Custom API Key Field
        custom_key_lbl = ctk.CTkLabel(self.custom_frame, text="Custom API Key (ถ้ามี):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        custom_key_lbl.pack(anchor="w", padx=0, pady=(5, 2))
        
        self.custom_api_key_entry = ctk.CTkEntry(
            self.custom_frame,
            placeholder_text="วาง API Key (ว่างได้หากใช้งานภายในเครื่อง เช่น Ollama)",
            show="*",
            height=32
        )
        self.custom_api_key_entry.insert(0, self.config_manager.get("custom_api_key", ""))
        self.custom_api_key_entry.pack(fill="x", padx=0, pady=(2, 8))
        self.custom_api_key_entry.bind("<FocusOut>", self._save_settings)
        
        # Custom Model Name Field
        custom_model_lbl = ctk.CTkLabel(self.custom_frame, text="ชื่อโมเดล (Model Name):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#BBBBBB")
        custom_model_lbl.pack(anchor="w", padx=0, pady=(5, 2))
        
        self.custom_model_entry = ctk.CTkEntry(
            self.custom_frame,
            placeholder_text="เช่น gpt-4o, llama3, deepseek-chat",
            height=32
        )
        self.custom_model_entry.insert(0, self.config_manager.get("custom_model", ""))
        self.custom_model_entry.pack(fill="x", padx=0, pady=(2, 10))
        self.custom_model_entry.bind("<FocusOut>", self._save_settings)
        
        # API Key Action Frame (Shared at the bottom of the card)
        key_actions = ctk.CTkFrame(self.ai_card, fg_color="transparent")
        key_actions.pack(fill="x", padx=20, pady=(10, 20))
        
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
        
        # Display the active settings frame
        self._toggle_provider_ui(saved_provider)

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

        # CARD 3: SENSITIVITY & VAD SETTINGS (Row 1, Column 0)
        self.vad_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        self.vad_card.grid(row=1, column=0, columnspan=1, padx=15, pady=15, sticky="nsew")
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
        
        # Strict interview question filter toggle
        self.strict_filter_switch = ctk.CTkSwitch(
            self.vad_card,
            text="คัดกรองเฉพาะคำถามสัมภาษณ์งานจริง (Strict Interview Filter)",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_strict_filter_changed
        )
        saved_strict = self.config_manager.get("strict_filter", True)
        if saved_strict:
            self.strict_filter_switch.select()
        else:
            self.strict_filter_switch.deselect()
        self.strict_filter_switch.grid(row=4, column=0, sticky="w", padx=20, pady=(15, 20))
        
        # Mini Mode Opacity slider
        opacity_frame = ctk.CTkFrame(self.vad_card, fg_color="transparent")
        opacity_frame.grid(row=4, column=1, sticky="ew", padx=20, pady=(5, 20))
        opacity_frame.grid_columnconfigure(0, weight=1)
        
        opacity_val = self.config_manager.get("mini_opacity", 0.90)
        self.opacity_label = ctk.CTkLabel(
            opacity_frame,
            text=f"ความโปร่งใสหน้าต่างลอย (Mini Opacity): {int(opacity_val * 100)}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#BBBBBB"
        )
        self.opacity_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        self.opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=0.20,
            to=1.00,
            number_of_steps=16,
            command=self._on_opacity_changed
        )
        self.opacity_slider.set(opacity_val)
        self.opacity_slider.grid(row=1, column=0, sticky="ew")
        
        # CARD 4: RESUME / PROFILE SETTINGS (Row 1, Column 1)
        self.resume_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        self.resume_card.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")
        self.resume_card.grid_columnconfigure(0, weight=1)
        
        resume_title = ctk.CTkLabel(
            self.resume_card,
            text="ประวัติและเรซูเม่ (Resume & Profile)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        resume_title.pack(anchor="w", padx=20, pady=(20, 5))
        
        resume_desc = ctk.CTkLabel(
            self.resume_card,
            text="อัปโหลดข้อมูลประวัติเพื่อช่วยให้ AI วิเคราะห์แนวทางคำตอบที่เข้ากับตัวคุณได้ดีที่สุด (ไม่เลือกไฟล์ก็ได้)",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            justify="left",
            wraplength=380
        )
        resume_desc.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Switch to enable resume analysis
        self.resume_switch = ctk.CTkSwitch(
            self.resume_card,
            text="เปิดใช้งานวิเคราะห์ประกอบการตอบคำถาม (Use Resume Context)",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_resume_toggle
        )
        saved_resume_enabled = self.config_manager.get("resume_enabled", False)
        if saved_resume_enabled:
            self.resume_switch.select()
        else:
            self.resume_switch.deselect()
        self.resume_switch.pack(anchor="w", padx=20, pady=(0, 10))
        
        # File selector and clear buttons frame
        btn_frame = ctk.CTkFrame(self.resume_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 5))
        
        self.upload_btn = ctk.CTkButton(
            btn_frame,
            text="📁 อัปโหลดไฟล์ (.pdf, .txt)",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            command=self._on_resume_upload
        )
        self.upload_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="ล้างข้อมูล",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#D9534F",
            hover_color="#C9302C",
            width=80,
            height=28,
            command=self._on_resume_clear
        )
        self.clear_btn.pack(side="left")
        
        # Filename indicator
        saved_filename = self.config_manager.get("resume_filename", "")
        self.filename_lbl = ctk.CTkLabel(
            self.resume_card,
            text=f"ไฟล์: {saved_filename}" if saved_filename else "ยังไม่ได้อัปโหลดไฟล์",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#888888"
        )
        self.filename_lbl.pack(anchor="w", padx=20, pady=(2, 8))
        
        # Textbox to paste or review resume text
        self.resume_textbox = ctk.CTkTextbox(
            self.resume_card,
            height=100,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.resume_textbox.pack(fill="both", expand=True, padx=20, pady=(2, 20))
        self.resume_textbox.insert("1.0", self.config_manager.get("resume_text", ""))
        self.resume_textbox.bind("<FocusOut>", self._save_resume_text)
        
    # =====================================================================
    # EVENT HANDLERS
    # =====================================================================
    
    def _on_provider_changed(self, selected_provider_thai):
        provider = "gemini" if selected_provider_thai == "Google Gemini" else "custom"
        self.config_manager.set("ai_provider", provider)
        self._toggle_provider_ui(provider)
        self._save_settings()
        print(f"[Settings Log] AI Provider changed to {provider}")
        
    def _toggle_provider_ui(self, provider):
        if provider == "gemini":
            self.custom_frame.pack_forget()
            self.gemini_frame.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.gemini_frame.pack_forget()
            self.custom_frame.pack(fill="x", padx=20, pady=(0, 10))

    def _save_settings(self, event=None):
        gemini_key = self.api_key_entry.get().strip()
        custom_base_url = self.custom_base_url_entry.get().strip()
        custom_key = self.custom_api_key_entry.get().strip()
        custom_model = self.custom_model_entry.get().strip()
        strict_filter = bool(self.strict_filter_switch.get())
        
        # Get resume settings
        resume_enabled = bool(self.resume_switch.get())
        resume_text = self.resume_textbox.get("1.0", "end-1c").strip()
        resume_filename = self.config_manager.get("resume_filename", "")
        
        self.config_manager.set("gemini_api_key", gemini_key)
        self.config_manager.set("custom_base_url", custom_base_url)
        self.config_manager.set("custom_api_key", custom_key)
        self.config_manager.set("custom_model", custom_model)
        self.config_manager.set("strict_filter", strict_filter)
        self.config_manager.set("resume_enabled", resume_enabled)
        self.config_manager.set("resume_text", resume_text)
        
        # Sync to analyzer
        provider = self.config_manager.get("ai_provider", "gemini")
        gemini_model = self.config_manager.get("gemini_model", "gemini-3.1-flash-lite")
        self.analyzer.update_provider_config(
            provider=provider,
            api_key=gemini_key,
            model_name=gemini_model,
            custom_api_key=custom_key,
            custom_base_url=custom_base_url,
            custom_model=custom_model,
            strict_filter=strict_filter,
            resume_enabled=resume_enabled,
            resume_text=resume_text
        )
        print("[Settings Log] AI settings saved and synced to analyzer.")

    def _on_strict_filter_changed(self):
        self._save_settings()
        print(f"[Settings Log] Strict interview filter toggled to {self.strict_filter_switch.get()}")

    def _on_test_api_key(self):
        # Save all settings first to ensure config and analyzer have the latest values
        self._save_settings()
        
        provider = self.config_manager.get("ai_provider", "gemini")
        if provider == "gemini":
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                self.key_status_lbl.configure(text="กรุณากรอก API Key ก่อนทดสอบ", text_color="#D9534F")
                return
        else:
            base_url = self.custom_base_url_entry.get().strip()
            if not base_url:
                self.key_status_lbl.configure(text="กรุณากรอก Base URL ก่อนทดสอบ", text_color="#D9534F")
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
        
    def _on_opacity_changed(self, value):
        val = round(float(value), 2)
        self.opacity_label.configure(text=f"ความโปร่งใสหน้าต่างลอย (Mini Opacity): {int(val * 100)}%")
        self.config_manager.set("mini_opacity", val)
        
        # Instantly update active window alpha if currently in mini mode
        try:
            root = self.winfo_toplevel()
            if hasattr(root, "is_mini_mode") and root.is_mini_mode:
                root.attributes("-alpha", val)
        except Exception as e:
            print(f"[Settings Log] Failed to update window alpha: {e}")
        
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
            
    def _on_resume_toggle(self):
        self._save_settings()
        
    def _save_resume_text(self, event=None):
        self._save_settings()
        
    def _on_resume_clear(self):
        self.resume_textbox.delete("1.0", "end")
        self.config_manager.set("resume_filename", "")
        self.filename_lbl.configure(text="ยังไม่ได้อัปโหลดไฟล์")
        self._save_settings()
        
    def _on_resume_upload(self):
        from tkinter import filedialog, messagebox
        import os
        
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์เรซูเม่ / ประวัติส่วนตัว",
            filetypes=[("Text & PDF Files", "*.txt *.pdf"), ("PDF Files", "*.pdf"), ("Text Files", "*.txt")]
        )
        if not file_path:
            return
            
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        text_content = ""
        
        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except Exception as e:
                try:
                    # fallback to ansi/cp1252 if utf-8 fails
                    with open(file_path, "r", encoding="ansi") as f:
                        text_content = f.read()
                except Exception as e2:
                    messagebox.showerror("Error", f"ไม่สามารถอ่านไฟล์ข้อความได้: {e}")
                    return
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages_text = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                text_content = "\n".join(pages_text)
                
                if not text_content.strip():
                    messagebox.showwarning("Warning", "ไม่พบข้อความในไฟล์ PDF นี้ (ไฟล์อาจเป็นรูปภาพสแกน)")
            except ImportError:
                messagebox.showerror("Error", "ไม่พบไลบรารี pypdf กรุณาติดตั้งโดยรันคำสั่ง pip install pypdf")
                return
            except Exception as e:
                messagebox.showerror("Error", f"ไม่สามารถอ่านไฟล์ PDF ได้: {e}")
                return
                
        if text_content:
            self.resume_textbox.delete("1.0", "end")
            self.resume_textbox.insert("1.0", text_content.strip())
            self.config_manager.set("resume_filename", filename)
            self.filename_lbl.configure(text=f"ไฟล์: {filename}")
            self._save_settings()
            messagebox.showinfo("Success", f"โหลดเรซูเม่จาก {filename} เรียบร้อยแล้ว (จำนวน {len(text_content)} ตัวอักษร)")
