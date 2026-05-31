import customtkinter as ctk
from .svg_images import icons

class NavigationFrame(ctk.CTkFrame):
    """
    Left navigation menu containing the app logo/title, navigation buttons,
    and a system status indicator at the bottom.
    Supports folding/collapsing into a compact 60px sidebar.
    """
    def __init__(self, parent, switch_page_callback, **kwargs):
        super().__init__(parent, width=220, corner_radius=0, fg_color="#18181A", **kwargs)
        self.switch_page_callback = switch_page_callback
        self.buttons = {}
        self.button_texts = {
            "dashboard": "หน้าหลัก",
            "history": "ประวัติการถาม",
            "settings": "การตั้งค่า",
            "guide": "คู่มือการใช้งาน"
        }
        self.is_collapsed = False
        
        # Lock frame size to width parameter
        self.grid_propagate(False)
        
        self.grid_rowconfigure(6, weight=1) # Empty space pushes status to bottom
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        
    def _build_ui(self):
        # App Title / Logo
        self.logo_label = ctk.CTkLabel(
            self,
            text=" Smart Answer",
            image=icons["brain"],
            compound="left",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00F0FF"
        )
        self.logo_label.grid(row=0, column=0, padx=(12, 32), pady=(25, 5), sticky="w")
        
        # Collapse / Expand Toggle Button
        self.collapse_btn = ctk.CTkButton(
            self,
            text="",
            image=icons["chevron_left"],
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#2B2B30",
            command=self.toggle_collapse
        )
        self.collapse_btn.grid(row=0, column=0, padx=(0, 8), pady=(25, 5), sticky="e")
        
        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Interview Prep Assistant",
            text_color="#888888",
            font=ctk.CTkFont(size=11, slant="italic")
        )
        self.subtitle_label.grid(row=1, column=0, padx=15, pady=(0, 25), sticky="w")
        
        # Navigation Buttons
        self._create_nav_button("dashboard", self.button_texts["dashboard"], icons["home"], row=2)
        self._create_nav_button("history", self.button_texts["history"], icons["history"], row=3)
        self._create_nav_button("settings", self.button_texts["settings"], icons["settings"], row=4)
        self._create_nav_button("guide", self.button_texts["guide"], icons["info"], row=5)
        
        # Status Card at the bottom
        self.status_card = ctk.CTkFrame(self, fg_color="#222224", corner_radius=8, height=75)
        self.status_card.grid(row=7, column=0, padx=8, pady=15, sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)
        
        self.status_dot = ctk.CTkLabel(
            self.status_card,
            text="●",
            text_color="#f0ad4e",  # Orange initially (loading/checking)
            font=ctk.CTkFont(size=14)
        )
        self.status_dot.grid(row=0, column=0, padx=(12, 5), pady=(12, 2), sticky="w")
        
        self.status_title = ctk.CTkLabel(
            self.status_card,
            text="กำลังเชื่อมต่อ...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF"
        )
        self.status_title.grid(row=0, column=0, padx=(28, 12), pady=(10, 2), sticky="w")
        
        self.status_desc = ctk.CTkLabel(
            self.status_card,
            text="กำลังตรวจจับไมโครโฟน",
            text_color="#888888",
            font=ctk.CTkFont(size=10),
            justify="left",
            wraplength=180
        )
        self.status_desc.grid(row=1, column=0, padx=(28, 12), pady=(0, 12), sticky="w")
        
        # Select Dashboard by default
        self.select_page("dashboard")
        
    def _create_nav_button(self, name, text, image, row):
        btn = ctk.CTkButton(
            self,
            text=" " + text,
            image=image,
            compound="left",
            height=40,
            corner_radius=6,
            border_spacing=10,
            fg_color="transparent",
            text_color="#CCCCCC",
            hover_color="#2B2B30",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._on_btn_click(name)
        )
        btn.grid(row=row, column=0, padx=8, pady=5, sticky="ew")
        self.buttons[name] = btn
        
    def _on_btn_click(self, name):
        self.select_page(name)
        self.switch_page_callback(name)
        
    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            # Shrink sidebar
            self.configure(width=60)
            # Remove title text
            self.logo_label.configure(text="", image=icons["brain"])
            self.logo_label.grid_configure(padx=15, sticky="")
            # Hide subtitle and status card
            self.subtitle_label.grid_remove()
            self.status_card.grid_remove()
            # Collapse buttons (hide text)
            for name, btn in self.buttons.items():
                btn.configure(text="", anchor="center")
                btn.grid_configure(padx=8)
            # Update toggle button
            self.collapse_btn.configure(image=icons["chevron_right"])
            self.collapse_btn.grid_configure(padx=0, sticky="")
        else:
            # Expand sidebar
            self.configure(width=220)
            # Restore title text
            self.logo_label.configure(text=" Smart Answer", image=icons["brain"])
            self.logo_label.grid_configure(padx=(12, 32), sticky="w")
            # Show subtitle and status card
            self.subtitle_label.grid()
            self.status_card.grid()
            # Expand buttons
            for name, btn in self.buttons.items():
                orig_text = self.button_texts[name]
                btn.configure(text=" " + orig_text, anchor="w")
                btn.grid_configure(padx=8)
            # Update toggle button
            self.collapse_btn.configure(image=icons["chevron_left"])
            self.collapse_btn.grid_configure(padx=(0, 8), sticky="e")
            
    def select_page(self, active_name):
        for name, btn in self.buttons.items():
            if name == active_name:
                btn.configure(
                    fg_color="#1F538D", 
                    text_color="#FFFFFF",
                    hover_color="#1F538D"
                )
            else:
                btn.configure(
                    fg_color="transparent", 
                    text_color="#CCCCCC",
                    hover_color="#2B2B30"
                )
                
    def set_status(self, title, dot_color="#28a745", desc=""):
        """Update the system status card in the sidebar."""
        self.status_title.configure(text=title)
        self.status_dot.configure(text_color=dot_color)
        if desc:
            self.status_desc.configure(text=desc)
