import customtkinter as ctk
from .coaching_card import create_coaching_card
from .svg_images import icons

class HistoryPage(ctk.CTkFrame):
    """
    History page that displays the saved interview questions list on the left 
    and details (Coaching Card) of the selected question on the right.
    """
    def __init__(self, parent, config_manager, **kwargs):
        super().__init__(parent, fg_color="#121214", **kwargs)
        self.config_manager = config_manager
        self.selected_item = None
        self.history_buttons = []
        self.rendered_card = None
        
        self.grid_columnconfigure(0, weight=0) # Left side: history list (320px)
        self.grid_columnconfigure(1, weight=1) # Right side: details
        self.grid_rowconfigure(0, weight=1)
        
        self._build_ui()
        
    def _build_ui(self):
        # LEFT LIST PANEL
        self.list_panel = ctk.CTkFrame(self, width=320, fg_color="#1E1E20", corner_radius=12)
        self.list_panel.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
        self.list_panel.grid_propagate(False)
        self.list_panel.grid_columnconfigure(0, weight=1)
        self.list_panel.grid_rowconfigure(2, weight=1) # History list stretches
        
        # Header / Title
        title_lbl = ctk.CTkLabel(
            self.list_panel,
            text=" ประวัติการสัมภาษณ์",
            image=icons["history"],
            compound="left",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        title_lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        desc_lbl = ctk.CTkLabel(
            self.list_panel,
            text="ประวัติคำถามที่เคยตรวจจับได้ สูงสุด 20 ข้อล่าสุด คลิกเพื่อดูการแนะนำย้อนหลัง",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            justify="left",
            wraplength=280
        )
        desc_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Scrollable list of history buttons
        self.history_scroll = ctk.CTkScrollableFrame(self.list_panel, fg_color="transparent")
        self.history_scroll.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.history_scroll.grid_columnconfigure(0, weight=1)
        
        # Clear History Button
        self.clear_btn = ctk.CTkButton(
            self.list_panel,
            text=" ล้างประวัติทั้งหมด",
            image=icons["trash"],
            compound="left",
            fg_color="transparent",
            text_color="#FF4136",
            hover_color="#302022",
            height=30,
            command=self._on_clear_history
        )
        self.clear_btn.grid(row=3, column=0, padx=15, pady=15, sticky="ew")
        
        # RIGHT DETAILS PANEL
        self.details_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.details_panel.grid(row=0, column=1, padx=(10, 15), pady=15, sticky="nsew")
        self.details_panel.grid_columnconfigure(0, weight=1)
        self.details_panel.grid_rowconfigure(0, weight=1)
        
        # Scrollable container for the Coaching Card details
        self.details_scroll = ctk.CTkScrollableFrame(self.details_panel, fg_color="#1E1E20", corner_radius=12)
        self.details_scroll.grid(row=0, column=0, sticky="nsew")
        self.details_scroll.grid_columnconfigure(0, weight=1)
        
        self.empty_state_lbl = None
        self.show_empty_details()

    def show_empty_details(self):
        """Displays a clean empty state prompt in the details panel."""
        if self.rendered_card:
            self.rendered_card.destroy()
            self.rendered_card = None
            
        if self.empty_state_lbl is None:
            self.empty_state_lbl = ctk.CTkLabel(
                self.details_scroll,
                text="กรุณาเลือกคำถามจากประวัติทางด้านซ้ายเพื่อดูรายละเอียดแนวทางการตอบ",
                font=ctk.CTkFont(size=14, slant="italic"),
                text_color="#666668"
            )
            self.empty_state_lbl.pack(pady=180)

    def load_history(self, history_items):
        """Populates the history list with interactive buttons."""
        # Clean current list buttons
        for btn in self.history_buttons:
            btn.destroy()
        self.history_buttons = []
        
        # Clean up empty label if items exist
        for child in self.history_scroll.winfo_children():
            child.destroy()
            
        if not history_items:
            no_hist_lbl = ctk.CTkLabel(
                self.history_scroll,
                text="ยังไม่มีข้อมูลประวัติคำถามสัมภาษณ์",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#666668"
            )
            no_hist_lbl.pack(pady=30)
            self.show_empty_details()
            return
            
        for idx, item in enumerate(history_items):
            q_text = item.get("question", "")
            lbl_text = f"{len(history_items) - idx}. " + (q_text[:35] + "..." if len(q_text) > 35 else q_text)
            
            # Highlight selected item
            is_active = (self.selected_item is not None and self.selected_item.get("question") == q_text)
            bg_color = "#2b2b30" if is_active else "#262629"
            text_col = "#00F0FF" if is_active else "#DDDDDD"
            
            if is_active:
                btn = ctk.CTkButton(
                    self.history_scroll,
                    text=lbl_text,
                    anchor="w",
                    fg_color=bg_color,
                    text_color=text_col,
                    hover_color="#2B2B30",
                    height=35,
                    border_width=1,
                    border_color="#1F538D",
                    corner_radius=6,
                    command=lambda val=item: self._on_item_clicked(val)
                )
            else:
                btn = ctk.CTkButton(
                    self.history_scroll,
                    text=lbl_text,
                    anchor="w",
                    fg_color=bg_color,
                    text_color=text_col,
                    hover_color="#2B2B30",
                    height=35,
                    border_width=0,
                    corner_radius=6,
                    command=lambda val=item: self._on_item_clicked(val)
                )
            btn.pack(fill="x", padx=4, pady=3)
            self.history_buttons.append(btn)
            
        # Re-render details for the selected item if it still exists in the history list
        if self.selected_item:
            found = False
            for item in history_items:
                if item.get("question") == self.selected_item.get("question"):
                    found = True
                    self.selected_item = item
                    break
            if not found:
                self.selected_item = None
                self.show_empty_details()
            else:
                self._render_details(self.selected_item)

    def _on_item_clicked(self, item):
        self.selected_item = item
        # Reload history to update active button styles (border/color)
        self.load_history(self.config_manager.get("history", []))
        self._render_details(item)
        
    def select_item_by_question_text(self, question_text):
        """Forces selection and viewing of a specific question (e.g. from app.py callbacks)."""
        history = self.config_manager.get("history", [])
        for item in history:
            if item.get("question") == question_text:
                self._on_item_clicked(item)
                break

    def _render_details(self, item):
        """Cleans details panel and draws the selected question's coaching card."""
        if self.empty_state_lbl:
            self.empty_state_lbl.destroy()
            self.empty_state_lbl = None
            
        if self.rendered_card:
            self.rendered_card.destroy()
            
        analysis = item.get("analysis", {})
        
        # Build new Coaching Card inside details_scroll
        self.rendered_card = create_coaching_card(
            self.details_scroll, 
            analysis, 
            card_label="ประวัติคำถามสัมภาษณ์"
        )
        self.rendered_card.pack(fill="x", padx=15, pady=15)

    def _on_clear_history(self):
        # We delegate UI confirmation to a callback or perform it here
        from tkinter import messagebox
        if messagebox.askyesno("ล้างประวัติ", "คุณแน่ใจหรือไม่ว่าต้องการล้างประวัติคำถามทั้งหมด?"):
            self.config_manager.clear_history()
            self.selected_item = None
            self.load_history([])
            self.show_empty_details()
