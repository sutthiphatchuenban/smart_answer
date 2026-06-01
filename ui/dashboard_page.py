import customtkinter as ctk
import threading
import time
from .svg_images import icons

class DashboardPage(ctk.CTkFrame):
    """
    Main Dashboard page containing the recording controls, volume visualizer,
    live transcript caption, and the scrollable coaching feed.
    """
    def __init__(self, parent, recorder, callbacks, **kwargs):
        super().__init__(parent, fg_color="#121214", **kwargs)
        self.recorder = recorder
        self.callbacks = callbacks
        
        # Waveform state
        self.is_recording = False
        self.current_volume_rms = 0.0
        self.waveform_data = [0.0] * 64
        self.waveform_lock = threading.Lock()
        self.waveform_dirty = False
        
        self.grid_columnconfigure(0, weight=0) # Left Control Panel (fixed width)
        self.grid_columnconfigure(1, weight=1) # Right Feed Area (stretches)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_ui()
        
        # Connect volume callback from recorder
        self.recorder.set_volume_callback(self._on_volume_update)
        
        # Start volume meter animation loop
        self._volume_meter_loop()

    def _build_ui(self):
        # LEFT CONTROL PANEL
        self.control_panel = ctk.CTkFrame(self, width=320, fg_color="#1E1E20", corner_radius=12)
        self.control_panel.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
        self.control_panel.grid_propagate(False) # Keep width fixed at 320
        self.control_panel.grid_columnconfigure(0, weight=1)
        
        ctrl_title = ctk.CTkLabel(
            self.control_panel,
            text="ควบคุมการดักฟัง",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        ctrl_title.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        ctrl_desc = ctk.CTkLabel(
            self.control_panel,
            text="เลือกระบบดักฟังและกดปุ่มด้านล่างเพื่อเริ่มฟังเสียงสัมภาษณ์",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            justify="left",
            wraplength=280
        )
        ctrl_desc.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        
        # Mode Selection Card
        mode_frame = ctk.CTkFrame(self.control_panel, fg_color="#262629", corner_radius=8)
        mode_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        mode_frame.grid_columnconfigure(0, weight=1)
        
        mode_lbl = ctk.CTkLabel(
            mode_frame,
            text="โหมดการทำงาน (Listening Mode):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#BBBBBB"
        )
        mode_lbl.grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")
        
        self.mode_switch = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Manual Mode", "Auto-Trigger"],
            height=30,
            command=self._on_mode_changed
        )
        self.mode_switch.set("Auto-Trigger")
        self.mode_switch.grid(row=1, column=0, padx=10, pady=(2, 12), sticky="ew")
        
        # Big Start / Stop Button
        self.record_btn = ctk.CTkButton(
            self.control_panel,
            text=" เริ่มจับสัญญาณเสียง",
            image=icons["mic"],
            compound="left",
            height=50,
            corner_radius=8,
            fg_color="#1F538D",
            hover_color="#14375E",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.callbacks['toggle_recording']
        )
        self.record_btn.grid(row=3, column=0, padx=15, pady=(20, 10), sticky="ew")
        
        # Waveform Card
        wave_frame = ctk.CTkFrame(self.control_panel, fg_color="#262629", corner_radius=8)
        wave_frame.grid(row=4, column=0, padx=15, pady=10, sticky="ew")
        wave_frame.grid_columnconfigure(0, weight=1)
        
        wave_lbl = ctk.CTkLabel(
            wave_frame,
            text="ระดับคลื่นเสียง (Audio Waveform):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#BBBBBB"
        )
        wave_lbl.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        
        self.waveform_canvas = ctk.CTkCanvas(
            wave_frame,
            height=60,
            bg="#262629",
            highlightthickness=0
        )
        self.waveform_canvas.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")
        
        # VAD Info Card
        vad_info_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        vad_info_frame.grid(row=5, column=0, padx=15, pady=15, sticky="ew")
        vad_info_frame.grid_columnconfigure(0, weight=1)
        
        self.vad_hint = ctk.CTkLabel(
            vad_info_frame,
            text="โหมดการทำงาน (Listening Mode):\n\n• Auto-Trigger:\nตรวจจับความเงียบและส่งวิเคราะห์คำตอบอัตโนมัติเมื่อพูดจบ (เหมาะกับคนพูดจังหวะปกติ)\n\n• Manual Mode:\nกดปุ่มเริ่ม/หยุดบันทึกเสียงด้วยตนเองเพื่อส่งวิเคราะห์ (เหมาะกับคนพูดช้า/เว้นช่องไฟนาน/เสียงรบกวนเยอะ)",
            font=ctk.CTkFont(size=11),
            text_color="#999999",
            justify="left",
            wraplength=260
        )
        self.vad_hint.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # RIGHT FEED AREA
        self.feed_area = ctk.CTkFrame(self, fg_color="transparent")
        self.feed_area.grid(row=0, column=1, padx=(10, 15), pady=15, sticky="nsew")
        self.feed_area.grid_columnconfigure(0, weight=1)
        self.feed_area.grid_rowconfigure(2, weight=1) # Scrollable Feed takes remaining space
        
        # Status Card (Header)
        self.header_card = ctk.CTkFrame(self.feed_area, fg_color="#1E1E20", corner_radius=10)
        self.header_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_card.grid_columnconfigure(0, weight=1)
        
        self.status_dot = ctk.CTkLabel(
            self.header_card,
            text="●",
            text_color="#28a745", # Green initially
            font=ctk.CTkFont(size=16)
        )
        self.status_dot.grid(row=0, column=0, padx=(18, 5), pady=(12, 3), sticky="w")
        
        self.status_title = ctk.CTkLabel(
            self.header_card,
            text="พร้อมดักฟังเสียงคำถามสัมภาษณ์",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        self.status_title.grid(row=0, column=0, padx=(35, 10), pady=(12, 3), sticky="w")
        
        self.status_desc = ctk.CTkLabel(
            self.header_card,
            text="กรุณากดปุ่มสีน้ำเงิน 'เริ่มจับสัญญาณเสียง' ทางด้านซ้ายเพื่อสแตนด์บายจับเสียง",
            text_color="#999999",
            font=ctk.CTkFont(size=11)
        )
        self.status_desc.grid(row=1, column=0, padx=(35, 10), pady=(0, 12), sticky="w")
        
        # Mini Mode Button
        self.mini_btn = ctk.CTkButton(
            self.header_card,
            text=" พับหน้าต่าง (Mini Mode)",
            image=icons["minimize"],
            compound="left",
            width=140,
            height=28,
            fg_color="#2B2B30",
            hover_color="#3A3A40",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.callbacks.get('toggle_mini_mode')
        )
        self.mini_btn.grid(row=0, column=0, padx=(0, 15), pady=(12, 0), sticky="ne")
        
        # Live Caption Box
        self.live_caption_card = ctk.CTkFrame(self.feed_area, fg_color="#1E1E20", height=95, corner_radius=10, border_width=1, border_color="#333335")
        self.live_caption_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.live_caption_card.grid_columnconfigure(0, weight=1)
        self.live_caption_card.grid_propagate(False)
        
        self.live_title_label = ctk.CTkLabel(
            self.live_caption_card,
            text=" LIVE TRANSCRIPT (กำลังฟังเสียงสดแบบเรียลไทม์...):",
            image=icons["live"],
            compound="left",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF4136"
        )
        self.live_title_label.grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")
        
        self.live_textbox = ctk.CTkTextbox(
            self.live_caption_card,
            height=45,
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=13, weight="normal"),
            wrap="word"
        )
        self.live_textbox.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="ew")
        self.live_textbox.insert("1.0", "ข้อความถอดเสียงแบบสดๆ จะแสดงขึ้นตรงนี้ทีละคำขณะที่คุณหรือผู้สัมภาษณ์กำลังพูด...")
        self.live_textbox.configure(state="disabled")
        
        # Restore button (hidden by default)
        self.restore_btn = ctk.CTkButton(
            self.live_caption_card,
            text=" ขยายหน้าต่าง",
            image=icons["maximize"],
            compound="left",
            width=100,
            height=24,
            fg_color="#1F538D",
            hover_color="#14375E",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.callbacks.get('toggle_mini_mode')
        )
        
        # Scrollable Coaching Feed
        self.feed_scroll = ctk.CTkScrollableFrame(self.feed_area, fg_color="transparent")
        self.feed_scroll.grid(row=2, column=0, sticky="nsew")
        self.feed_scroll.grid_columnconfigure(0, weight=1)
        
        # Empty State Label
        self.empty_feed_label = None
        self.show_empty_state()
        
    # =====================================================================
    # MINI WINDOW MODE TOGGLE
    # =====================================================================
    
    def set_mini_mode(self, enabled: bool):
        if enabled:
            self.control_panel.grid_remove()
            self.header_card.grid_remove()
            
            # Configure feed_area grid weights for mini mode
            self.feed_area.grid_rowconfigure(0, weight=0) # live_caption_card
            self.feed_area.grid_rowconfigure(1, weight=1) # feed_scroll
            self.feed_area.grid_rowconfigure(2, weight=0) # empty
            
            # Reposition caption card
            self.feed_area.grid_configure(padx=10, pady=10)
            self.live_caption_card.grid_configure(row=0, pady=(0, 5))
            self.live_caption_card.configure(height=90)
            self.live_textbox.configure(height=45)
            
            # Position feed_scroll below the caption card
            self.feed_scroll.grid(row=1, column=0, sticky="nsew")
            
            # Show restore button
            self.restore_btn.grid(row=0, column=0, padx=15, pady=(8, 2), sticky="e")
        else:
            self.control_panel.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
            self.header_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
            
            # Configure feed_area grid weights for normal mode
            self.feed_area.grid_rowconfigure(0, weight=0) # header_card
            self.feed_area.grid_rowconfigure(1, weight=0) # live_caption_card
            self.feed_area.grid_rowconfigure(2, weight=1) # feed_scroll
            
            # Restore feed_scroll to row 2
            self.feed_scroll.grid(row=2, column=0, sticky="nsew")
            
            # Restore caption card layout
            self.feed_area.grid_configure(padx=(10, 15), pady=15)
            self.live_caption_card.grid_configure(row=1, pady=(0, 10))
            self.live_caption_card.configure(height=95)
            self.live_textbox.configure(height=45)
            
            # Hide restore button
            self.restore_btn.grid_remove()

    # =====================================================================
    # INTERFACE UPDATE METHODS (Called from app.py)
    # =====================================================================
    
    def update_live_caption(self, text):
        self.live_textbox.configure(state="normal")
        self.live_textbox.delete("1.0", "end")
        self.live_textbox.insert("1.0", text)
        self.live_textbox.configure(state="disabled")
        
    def hide_empty_state(self):
        if self.empty_feed_label:
            self.empty_feed_label.destroy()
            self.empty_feed_label = None
            
    def show_empty_state(self):
        if self.empty_feed_label is None:
            self.empty_feed_label = ctk.CTkLabel(
                self.feed_scroll,
                text="ยังไม่มีคำถามตรวจจับได้ในเซสชันนี้...\nเมื่อจับประโยคที่เป็นคำถามได้ คำแนะนำและแนวทางนำเสนอคำตอบจะปรากฏตรงนี้โดยอัตโนมัติ",
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color="#666668"
            )
            self.empty_feed_label.pack(pady=120)
            
    def scroll_feed_to_bottom(self):
        self.feed_scroll.after(150, lambda: self.feed_scroll._parent_canvas.yview_moveto(1.0))
        
    def set_recording_state(self, is_recording):
        self.is_recording = is_recording
        if not is_recording:
            with self.waveform_lock:
                self.waveform_data = [0.0] * len(self.waveform_data)
                self.waveform_dirty = True
            self._draw_waveform()
            
    def update_record_button(self, is_recording, mode="auto"):
        if is_recording:
            self.record_btn.configure(
                text=" หยุดการจับเสียง" if mode == "manual" else " หยุดดักจับอัตโนมัติ",
                image=icons["stop"],
                fg_color="#D9534F",
                hover_color="#C9302C"
            )
        else:
            self.record_btn.configure(
                text=" เริ่มจับสัญญาณเสียง",
                image=icons["mic"],
                fg_color="#1F538D",
                hover_color="#14375E"
            )
            
    # =====================================================================
    # INTERACTIVE CALLBACKS
    # =====================================================================
    
    def _on_mode_changed(self, mode):
        new_mode = "manual" if mode == "Manual Mode" else "auto"
        print(f"Recording mode changed to {new_mode}")
        if self.is_recording:
            # Toggle off and on to apply changes immediately
            self.callbacks['toggle_recording']()
            self.callbacks['toggle_recording']()
            
    # =====================================================================
    # WAVEFORM VISUALIZER & VOLUME METER
    # =====================================================================
    
    def _on_volume_update(self, rms, waveform_chunk=None):
        val = min(1.0, rms * 15.0)
        self.current_volume_rms = val
        
        if waveform_chunk:
            # We display waveform when system or mic audio is captured
            # Downsample from 32 points to 16 points to match the 64-point canvas width
            chunk_16 = waveform_chunk[::2]
            with self.waveform_lock:
                self.waveform_data = self.waveform_data[len(chunk_16):] + chunk_16
                self.waveform_dirty = True
                
    def _draw_waveform(self):
        self.waveform_canvas.delete("all")
        
        w = self.waveform_canvas.winfo_width()
        h = self.waveform_canvas.winfo_height()
        
        if w < 10:  # Canvas not rendered yet
            return
            
        with self.waveform_lock:
            waveform_data = list(self.waveform_data)
            self.waveform_dirty = False
            
        points_count = len(waveform_data)
        dx = w / (points_count - 1)
        mid_y = h / 2
        
        # Center line
        self.waveform_canvas.create_line(0, mid_y, w, mid_y, fill="#3A3A3F", width=1)
        
        active_color = "#00F0FF" if self.is_recording else "#55555A"
        
        # Draw SoundCloud style symmetric bars
        for i, val in enumerate(waveform_data):
            x = i * dx
            amp = abs(val) * 1.8 * mid_y
            amp = min(mid_y - 2, amp)
            
            if amp > 1.5:
                self.waveform_canvas.create_line(
                    x, mid_y - amp, x, mid_y + amp,
                    fill=active_color,
                    width=2
                )
            else:
                self.waveform_canvas.create_line(
                    x, mid_y - 1, x, mid_y + 1,
                    fill="#3A3A3F",
                    width=2
                )
                
    def _volume_meter_loop(self):
        # If the page is currently hidden (not mapped), pause updating to save resources
        if not self.winfo_ismapped():
            self.after(200, self._volume_meter_loop)
            return

        should_draw = False
        if self.is_recording:
            with self.waveform_lock:
                if self.waveform_dirty or any(abs(val) > 0.001 for val in self.waveform_data):
                    # Decay sound data slowly over time
                    self.waveform_data = [val * 0.85 for val in self.waveform_data]
                    should_draw = True
        else:
            with self.waveform_lock:
                if any(val != 0.0 for val in self.waveform_data):
                    self.waveform_data = [0.0] * len(self.waveform_data)
                    should_draw = True
                    
        if should_draw:
            self._draw_waveform()
            
        self.after(60, self._volume_meter_loop)
