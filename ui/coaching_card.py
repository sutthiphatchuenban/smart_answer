import customtkinter as ctk
from .svg_images import icons


def create_coaching_card(parent, result, card_label=""):
    """
    Creates a coaching card widget displaying Gemini analysis results.
    
    Args:
        parent: The parent CTk widget (typically a scrollable frame).
        result: Dict with Gemini analysis data (question_thai, category, focus_areas,
                key_points, answer_strategy, star_framework, example_outline, suggested_answer).
        card_label: Label prefix for the card header (e.g. "#1", "History").
    
    Returns:
        The card CTkFrame widget.
    """
    # Build card frame
    card = ctk.CTkFrame(parent, fg_color="#1E1E1E", corner_radius=10, border_width=1, border_color="#333333")
    card.pack(fill="x", padx=10, pady=10)
    card.grid_columnconfigure(0, weight=1)

    # Header Frame
    q_thai = result.get("question_thai") or "คำถามสัมภาษณ์"
    category = result.get("category") or "ทั่วไป"
    
    header_frame = ctk.CTkFrame(card, fg_color="#2b2b2b", corner_radius=8)
    header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
    header_frame.grid_columnconfigure(0, weight=1)

    q_label = ctk.CTkLabel(
        header_frame,
        text=f"  {card_label}: {q_thai}",
        image=icons["question"],
        compound="left",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color="#00F0FF",
        anchor="w",
        justify="left",
        wraplength=600
    )
    q_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")

    cat_badge = ctk.CTkLabel(
        header_frame,
        text=category,
        fg_color="#1f538d",
        corner_radius=4,
        padx=10,
        pady=3,
        font=ctk.CTkFont(size=10, weight="bold")
    )
    cat_badge.grid(row=0, column=1, padx=12, pady=8, sticky="e")

    # Focus areas display (comma separated list with bullet symbol for responsiveness)
    focus_areas = result.get("focus_areas", [])
    if focus_areas:
        focus_text = "  จุดประสงค์ผู้ถาม:  " + "  •  ".join(focus_areas)
        focus_lbl = ctk.CTkLabel(
            card,
            text=focus_text,
            image=icons["target"],
            compound="left",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888888",
            anchor="w",
            justify="left",
            wraplength=780
        )
        focus_lbl.grid(row=1, column=0, sticky="w", padx=15, pady=(2, 6))

    # Coaching Sections Content
    content_frame = ctk.CTkFrame(card, fg_color="transparent")
    content_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 10))
    content_frame.grid_columnconfigure(0, weight=1)

    # 1. Suggested Answer (First, high-contrast box)
    ans_text = result.get("suggested_answer")
    ans_row_offset = 0
    if ans_text:
        ans_box = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=6, border_width=1, border_color="#3a3a3a")
        ans_box.grid(row=0, column=0, sticky="ew", pady=(5, 10))
        ans_box.grid_columnconfigure(0, weight=1)
        
        ans_title = ctk.CTkLabel(ans_box, text="  ตัวอย่างคำตอบที่แนะนำ (Suggested Answer):", image=icons["chat"], compound="left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ECC71", anchor="w", justify="left")
        ans_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        
        ans_desc = ctk.CTkLabel(ans_box, text=ans_text, font=ctk.CTkFont(size=13, weight="normal"), justify="left", anchor="w", wraplength=670, text_color="#FFFFFF")
        ans_desc.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))
        ans_row_offset = 1

    # 2. Key Points to Answer
    kp_label = ctk.CTkLabel(content_frame, text="  ประเด็นสำคัญที่ควรตอบ (Key Points):", image=icons["bulb"], compound="left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F39C12")
    kp_label.grid(row=ans_row_offset + 0, column=0, sticky="w", pady=(5, 2))
    
    kp_text = ""
    for kp in result.get("key_points", []):
        kp_text += f"• {kp}\n"
    if not kp_text:
        kp_text = "ไม่มีข้อมูลหัวข้อคำตอบ"
        
    kp_desc = ctk.CTkLabel(content_frame, text=kp_text.strip(), font=ctk.CTkFont(size=12), justify="left", anchor="w", wraplength=700)
    kp_desc.grid(row=ans_row_offset + 1, column=0, sticky="w", padx=10, pady=(0, 5))

    # 3. Answer Strategy
    strat_label = ctk.CTkLabel(content_frame, text="  กลยุทธ์การนำเสนอ/ข้อควรระวัง (Strategy):", image=icons["target"], compound="left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498DB")
    strat_label.grid(row=ans_row_offset + 2, column=0, sticky="w", pady=(5, 2))
    
    strat_desc = ctk.CTkLabel(content_frame, text=result.get("answer_strategy") or "ไม่มีกลยุทธ์เฉพาะ", font=ctk.CTkFont(size=12), justify="left", anchor="w", wraplength=700)
    strat_desc.grid(row=ans_row_offset + 3, column=0, sticky="w", padx=10, pady=(0, 5))

    # 4. STAR Framework
    star = result.get("star_framework")
    curr_row = ans_row_offset + 4
    if star and (star.get("situation") or star.get("task") or star.get("action") or star.get("result")):
        star_label = ctk.CTkLabel(content_frame, text="  โครงสร้างคำตอบแบบ STAR (STAR Framework):", image=icons["star"], compound="left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ECC71")
        star_label.grid(row=curr_row, column=0, sticky="w", pady=(5, 2))
        
        star_text = ""
        if star.get("situation"):
            star_text += f"S - Situation (สถานการณ์): {star['situation']}\n"
        if star.get("task"):
            star_text += f"T - Task (งาน/เป้าหมาย): {star['task']}\n"
        if star.get("action"):
            star_text += f"A - Action (การลงมือทำ): {star['action']}\n"
        if star.get("result"):
            star_text += f"R - Result (ผลลัพธ์/บทเรียน): {star['result']}\n"
            
        star_desc = ctk.CTkLabel(content_frame, text=star_text.strip(), font=ctk.CTkFont(size=12), justify="left", anchor="w", wraplength=700)
        star_desc.grid(row=curr_row+1, column=0, sticky="w", padx=10, pady=(0, 5))
        curr_row += 2

    # 5. Example Outline
    outline = result.get("example_outline")
    if outline:
        out_label = ctk.CTkLabel(content_frame, text="  ลำดับการตอบคำถาม (Example Outline):", image=icons["list"], compound="left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#E74C3C")
        out_label.grid(row=curr_row, column=0, sticky="w", pady=(5, 2))
        
        out_text = ""
        for i, item in enumerate(outline):
            out_text += f"{i+1}. {item}\n"
            
        out_desc = ctk.CTkLabel(content_frame, text=out_text.strip(), font=ctk.CTkFont(size=12), justify="left", anchor="w", wraplength=700)
        out_desc.grid(row=curr_row+1, column=0, sticky="w", padx=10, pady=(0, 10))

    return card
