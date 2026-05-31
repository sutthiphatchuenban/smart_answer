import os
import customtkinter as ctk
from PIL import Image
from ui.svg_images import get_svg_image, SVG_BRAIN

def generate_ico():
    print("Rendering SVG_BRAIN to PIL Image...")
    # Render at 256x256 size for high-quality ICO scaling
    ctk_img = get_svg_image(SVG_BRAIN, size=(256, 256))
    pil_img = ctk_img._light_image
    
    if pil_img:
        ico_path = "app_icon.ico"
        print(f"Saving to {ico_path} with standard icon sizes...")
        pil_img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
        print("Success! app_icon.ico has been generated.")
    else:
        print("Error: Failed to render SVG logo.")

if __name__ == "__main__":
    # CustomTkinter needs a tk context initialized to load images,
    # but since get_svg_image runs pure math on svglib/PIL and returns a CTkImage,
    # let's run it.
    generate_ico()
