import customtkinter as ctk
from .svg_images import icons

class GuidePage(ctk.CTkFrame):
    """
    Dedicated Help/Guide page explaining how to use all features of the application.
    Structured in beautifully styled cards inside a scrollable frame.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#121214", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_ui()
        
    def _build_ui(self):
        # Scrollable container for instructions
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # TITLE HEADER
        title_card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E1E20", corner_radius=12)
        title_card.grid(row=0, column=0, padx=10, pady=(10, 15), sticky="ew")
        title_card.grid_columnconfigure(0, weight=1)
        
        title_lbl = ctk.CTkLabel(
            title_card,
            text=" คู่มือการใช้งานโปรแกรม (User Guide)",
            image=icons["info"],
            compound="left",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00F0FF"
        )
        title_lbl.pack(anchor="w", padx=20, pady=(20, 5))
        
        desc_lbl = ctk.CTkLabel(
            title_card,
            text="ยินดีต้อนรับสู่ Smart Answer! หน้านี้จะแนะนำวิธีตั้งค่าและใช้งานทุกฟีเจอร์ภายในโปรแกรมเพื่อให้พร้อมสำหรับการสัมภาษณ์งานจริงอย่างมืออาชีพ",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            justify="left",
            wraplength=750
        )
        desc_lbl.pack(anchor="w", padx=20, pady=(0, 20))
        
        # CARD 1: แนะนำฟังก์ชันพื้นฐาน
        row = 1
        self._create_guide_card(
            title="1. เริ่มต้นใช้งานและตั้งค่าโมเดล AI",
            desc="โปรแกรมรองรับการวิเคราะห์ประมวลผลผ่านปัญญาประดิษฐ์ 2 ช่องทาง โดยสามารถเข้าไปกำหนดค่าในหน้า 'การตั้งค่า':\n\n"
                 "• Google Gemini (แนะนำ):\n"
                 "  กรอกคีย์เปิดใช้งาน API Key (รับฟรีจาก Google AI Studio) และเลือกรุ่นโมเดลที่แนะนำ เช่น gemini-3.1-flash-lite เพื่อความเร็วสูง\n\n"
                 "• Custom OpenAI (ทางเลือก):\n"
                 "  รองรับ API ภายนอกอื่นๆ หรือโมเดลที่รันบนเครื่องตนเอง (เช่น Ollama หรือ DeepSeek) โดยการกรอก Base URL (Endpoint), คีย์ และชื่อโมเดล",
            icon=icons["settings"],
            row=row
        )
        
        # CARD 2: ระบบเสียงและอุปกรณ์ดักจับ
        row += 1
        self._create_guide_card(
            title="2. แหล่งสัญญาณเสียงและอุปกรณ์ดักจับ (Audio Inputs)",
            desc="ในหน้า 'การตั้งค่า' คุณสามารถเลือกว่าจะใช้สัญญาณเสียงประเภทใด:\n\n"
                 "• โหมดไมโครโฟน (Microphone):\n"
                 "  สำหรับดักจับเสียงพูดของตัวคุณเองหรือเสียงพูดผ่านไมค์ภายนอก\n\n"
                 "• โหมดเสียงระบบ/ลำโพง (System Audio / WASAPI Loopback):\n"
                 "  ดักฟังเสียงจากโปรแกรมแชทประชุมออนไลน์โดยตรง (Zoom, MS Teams, Google Meet, Discord ฯลฯ) ผ่าน WASAPI Loopback ของ Windows เพื่อความเสถียรและตัดเสียงกวนรอบทิศทางภายนอก\n\n"
                 "• ระบบลดเสียงรบกวน (Noise Reduction):\n"
                 "  กรองเสียงฮัมและคลื่นความถี่รบกวนผ่านอัลกอริทึม STFT Spectral Subtraction ก่อนส่งถอดความ",
            icon=icons["speaker"],
            row=row
        )
        
        # CARD 3: โหมดตรวจจับเสียงพูด (VAD Modes)
        row += 1
        self._create_guide_card(
            title="3. โหมดจับสัญญาณเสียงพูด (Listening Modes)",
            desc="บนหน้าจอ 'หน้าหลัก' คุณสามารถสลับโหมดการทำงานได้ดังนี้:\n\n"
                 "• โหมดอัตโนมัติ (Auto-Trigger):\n"
                 "  โปรแกรมจะทำการวัดระดับความเงียบรอบตัว (Noise Calibration) เป็นเวลา 1.2 วินาทีเมื่อเริ่มฟัง จากนั้นจะทำหน้าที่ดักจับเสียงพูดและส่งไปประมวลผลทันทีหลังจากผู้พูดหยุดพูดสักระยะโดยอัตโนมัติ (ปรับแต่ง VAD cap ป้องกันสัญญาณขัดจังหวะในห้องเสียงดังสูงสุดถึง 0.080)\n\n"
                 "• โหมดแมนนวล (Manual Mode):\n"
                 "  กดปุ่ม 'เริ่มจับสัญญาณเสียง' (หรือปุ่มลัด Spacebar) เพื่ออัดเสียง และกดอีกครั้งเพื่อหยุดส่งไปวิเคราะห์ เหมาะสำหรับสภาพแวดล้อมที่ห้องเสียงดังมาก หรือผู้สัมภาษณ์พูดช้า/มีจังหวะหยุดคิดค่อนข้างนาน",
            icon=icons["mic"],
            row=row
        )
        
        # CARD 4: การใช้งานเรซูเม่อ้างอิง (Resume Context)
        row += 1
        self._create_guide_card(
            title="4. ระบบอ้างอิงข้อมูลเรซูเม่ (Resume & Profile)",
            desc="เพื่อให้ AI ร่างคำตอบที่สอดคล้องกับคุณมากที่สุด คุณสามารถเชื่อมโยงเรซูเม่ประวัติส่วนตัวได้ในการตั้งค่า:\n\n"
                 "• เปิดสวิตช์ 'เปิดใช้งานวิเคราะห์ประกอบการตอบคำถาม' (Use Resume Context)\n"
                 "• อัปโหลดไฟล์ประวัติส่วนตัวในรูปแบบไฟล์ PDF (.pdf) หรือไฟล์ข้อความ (.txt) ซึ่งระบบจะสกัดข้อความมาใส่ในโปรแกรม หรือพิมพ์/วางรายละเอียดเรซูเม่ลงในกล่องรับข้อมูลโดยตรง\n"
                 "• เมื่อใช้งาน AI จะปรับแต่งทักษะ โครงสร้างเรื่องเล่าเชิงพฤติกรรม (STAR Framework) และตัวอย่างคำตอบให้อิงตามประวัติการทำงานของคุณเพื่อให้ตอบคำถามได้จริงและมีระดับมืออาชีพสูงสุด",
            icon=icons["bulb"],
            row=row
        )
        
        # CARD 5: การใช้งานหน้าต่างลอยย่อส่วน (Mini Mode)
        row += 1
        self._create_guide_card(
            title="5. หน้าต่างลอยย่อส่วนขนาดจิ๋ว (Mini Mode Overlay)",
            desc="เพื่อใช้ฝึกซ้อมในขณะเปิดโปรแกรมสัมภาษณ์ออนไลน์บนหน้าจอหลัก คุณสามารถสลับรูปแบบ UI เป็นหน้าต่างขนาดจิ๋วได้:\n\n"
                 "• คลิกปุ่ม 'สลับหน้าต่างลอย' ที่มุมขวาบนของหน้าหลัก\n"
                 "• หน้าต่างจะปักหมุดไว้ที่ระดับบนสุดของหน้าจอเสมอ (Always on Top) เพื่อให้อ่านคำแนะนำได้ตลอดเวลา\n"
                 "• สามารถลากเพื่อปรับย่อ/ขยายขนาดของหน้าต่างได้อย่างอิสระ (Resizable) โดยตัวหนังสือและโครงสร้างคำตอบจะทำการปัดบรรทัดและจัดข้อความให้สมบูรณ์ตามขนาดหน้าต่าง (Auto-wrap)\n"
                 "• แถบความโปร่งใส (Opacity Slider) ในหน้าตั้งค่าช่วยให้เลื่อนปรับความจางของหน้าต่างได้ตั้งแต่ 20% ถึง 100% เพื่อไม่ให้บดบังเนื้อหาสำคัญเบื้องหลัง",
            icon=icons["chat"],
            row=row
        )
        
        # CARD 6: ปุ่มคีย์ลัดและขนาดหน้าจอ (Shortcuts & Zoom)
        row += 1
        self._create_guide_card(
            title="6. คีย์ลัดแป้นพิมพ์และระบบซูมขยายหน้าจอ (Shortcuts & Zoom)",
            desc="เพื่ออำนวยความสะดวกในการใช้งานบนหน้าจอคอมพิวเตอร์ขนาดใหญ่หรือเมื่อเร่งรีบสัมภาษณ์:\n\n"
                 "• ปุ่มลัดควบคุมเสียง (Manual Mode):\n"
                 "  กดปุ่ม Spacebar (คีย์เว้นวรรค) เพื่อเริ่ม/หยุดการอัดเสียงในโหมด Manual ได้ทันทีโดยไม่ต้องคลิกเมาส์\n\n"
                 "• ปุ่มลัดสำหรับระบบซูมหน้าจอ (Zoom System):\n"
                 "  - กด Ctrl + '+' (หรือ Ctrl + '=') : เพื่อขยายขนาดตัวหนังสือและปุ่มต่างๆ ให้ใหญ่ขึ้น\n"
                 "  - กด Ctrl + '-' : เพื่อลดระดับการขยายตัวหนังสือและปุ่มต่างๆ ให้เล็กลง\n"
                 "  - กด Ctrl + '0' : เพื่อรีเซ็ตขนาดตัวหนังสือและวิดเจ็ตทั้งหมดกลับเป็นมาตรฐาน\n"
                 "  *หมายเหตุ: โปรแกรมจะบันทึกระดับการซูมล่าสุดของคุณไว้ และนำไปใช้เมื่อเปิดรันโปรแกรมในครั้งต่อไปโดยอัตโนมัติ*",
            icon=icons["star"],
            row=row
        )
        
    def _create_guide_card(self, title, desc, icon, row):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E1E20", corner_radius=12)
        card.grid(row=row, column=0, padx=10, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        
        # Header inside card
        header = ctk.CTkFrame(card, fg_color="#262629", corner_radius=8)
        header.pack(fill="x", padx=12, pady=(12, 10))
        header.grid_columnconfigure(0, weight=1)
        
        title_lbl = ctk.CTkLabel(
            header,
            text=f"  {title}",
            image=icon,
            compound="left",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00F0FF"
        )
        title_lbl.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        
        # Desc body
        body_lbl = ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=12),
            text_color="#DDDDDD",
            justify="left",
            anchor="w"
        )
        body_lbl.pack(fill="x", padx=24, pady=(0, 20))
        
        # Bind resize configure to enable responsive auto-wrap
        card._last_width = 0
        card._resize_timer_id = None
        
        def _update_wrap():
            card._resize_timer_id = None
            try:
                scaling = card._get_widget_scaling()
            except Exception:
                scaling = 1.0
            virtual_width = card.winfo_width() / scaling
            wrap_w = max(100, virtual_width - 48)
            try:
                body_lbl.configure(wraplength=wrap_w)
            except Exception:
                pass

        def _on_resize(event):
            # Only handle configure events for the card frame itself, not children
            if event.widget != card:
                return
                
            card_width = event.width
            
            # If it's the first render, update immediately
            if card._last_width == 0:
                card._last_width = card_width
                _update_wrap()
                return
                
            # Skip minor/jitter resize updates
            if abs(card_width - card._last_width) < 15:
                return
            card._last_width = card_width
            
            # Cancel previous scheduled update to debounce
            if card._resize_timer_id is not None:
                try:
                    card.after_cancel(card._resize_timer_id)
                except Exception:
                    pass
                    
            # Schedule wrapping after 100ms pause in resizing
            card._resize_timer_id = card.after(100, _update_wrap)
            
        card.bind("<Configure>", _on_resize)
