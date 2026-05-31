import io
import customtkinter as ctk
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image

def get_svg_image(svg_content: str, size=(20, 20)) -> ctk.CTkImage:
    """
    Renders an inline SVG string into a PIL Image using svglib with transparent background
    by performing dual rendering (black & white canvases) to compute the alpha channel.
    """
    try:
        f = io.BytesIO(svg_content.encode('utf-8'))
        drawing = svg2rlg(f)
        if drawing is None:
            raise ValueError("svglib failed to parse SVG content")
            
        # Draw SVG on black background
        png_black = renderPM.drawToString(drawing, fmt='PNG', bg=0x000000)
        img_black = Image.open(io.BytesIO(png_black)).convert("RGB")
        
        # Draw SVG on white background
        png_white = renderPM.drawToString(drawing, fmt='PNG', bg=0xffffff)
        img_white = Image.open(io.BytesIO(png_white)).convert("RGB")
        
        # Apply alpha extraction
        pixels_black = img_black.load()
        pixels_white = img_white.load()
        
        width, height = img_black.size
        rgba_data = []
        for y in range(height):
            for x in range(width):
                r_b, g_b, b_b = pixels_black[x, y]
                r_w, g_w, b_w = pixels_white[x, y]
                
                # Calculate alpha channel: 255 - (white - black)
                a_r = 255 - (r_w - r_b)
                a_g = 255 - (g_w - g_b)
                a_b = 255 - (b_w - b_b)
                a = min(a_r, a_g, a_b)
                a = max(0, min(255, a))
                
                if a > 0:
                    r = min(255, int(r_b * 255 / a))
                    g = min(255, int(g_b * 255 / a))
                    b = min(255, int(b_b * 255 / a))
                else:
                    r, g, b = 0, 0, 0
                rgba_data.append((r, g, b, a))
                
        img = Image.new("RGBA", (width, height))
        img.putdata(rgba_data)
        
        # Return CTkImage with correct display size
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception as e:
        print(f"[SVG Log] Error rendering SVG: {e}")
        # Fallback to an empty transparent image in case of render error
        fallback_img = Image.new("RGBA", size, (0, 0, 0, 0))
        return ctk.CTkImage(light_image=fallback_img, dark_image=fallback_img, size=size)

# SVG templates with white stroke for Dark Mode buttons
SVG_HOME = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>"""

SVG_HISTORY = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>"""

SVG_SETTINGS = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>"""

SVG_MIC = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" x2="12" y1="19" y2="22"/></svg>"""

SVG_MIC_WHITE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" x2="12" y1="19" y2="22"/></svg>"""

SVG_SPEAKER = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>"""

SVG_STOP = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>"""

# New SVGs for emoji replacement
SVG_BRAIN = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="4.5" y="4.5" width="15" height="15" rx="5" stroke="#0091FF" stroke-width="4.5" /></svg>"""


SVG_BULB = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F39C12" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .5 2.2 1.5 3 .7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>"""

SVG_TARGET = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3498DB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>"""

SVG_CHAT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2ECC71" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>"""

SVG_STAR = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F1C40F" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>"""

SVG_LIST = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E74C3C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>"""

SVG_QUESTION = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""

SVG_LIVE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF4136" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/></svg>"""

SVG_TRASH = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF4136" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>"""

SVG_CHEVRON_LEFT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>"""

SVG_CHEVRON_RIGHT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>"""

SVG_MINIMIZE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></svg>"""

SVG_MAXIMIZE = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>"""

SVG_INFO = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>"""

# Pre-compiled CTkImages
icons = {
    "home": get_svg_image(SVG_HOME, size=(18, 18)),
    "history": get_svg_image(SVG_HISTORY, size=(18, 18)),
    "settings": get_svg_image(SVG_SETTINGS, size=(18, 18)),
    "mic": get_svg_image(SVG_MIC, size=(18, 18)),
    "mic_white": get_svg_image(SVG_MIC_WHITE, size=(18, 18)),
    "speaker": get_svg_image(SVG_SPEAKER, size=(18, 18)),
    "stop": get_svg_image(SVG_STOP, size=(18, 18)),
    "brain": get_svg_image(SVG_BRAIN, size=(22, 22)),
    "bulb": get_svg_image(SVG_BULB, size=(18, 18)),
    "target": get_svg_image(SVG_TARGET, size=(18, 18)),
    "chat": get_svg_image(SVG_CHAT, size=(18, 18)),
    "star": get_svg_image(SVG_STAR, size=(18, 18)),
    "list": get_svg_image(SVG_LIST, size=(18, 18)),
    "question": get_svg_image(SVG_QUESTION, size=(18, 18)),
    "live": get_svg_image(SVG_LIVE, size=(18, 18)),
    "trash": get_svg_image(SVG_TRASH, size=(16, 16)),
    "chevron_left": get_svg_image(SVG_CHEVRON_LEFT, size=(14, 14)),
    "chevron_right": get_svg_image(SVG_CHEVRON_RIGHT, size=(14, 14)),
    "minimize": get_svg_image(SVG_MINIMIZE, size=(16, 16)),
    "maximize": get_svg_image(SVG_MAXIMIZE, size=(16, 16)),
    "info": get_svg_image(SVG_INFO, size=(18, 18)),
}

