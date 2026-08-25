"""
KBA Icon Generator
সব icon ফাইল তৈরি করবে।
একবার চালালেই সব icon রিজেনারেট হয়ে যাবে।
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ডিজাইন কনফিগ
BG_COLOR    = "#0C447C"
TEXT_COLOR   = "#FFFFFF"
ACCENT_COLOR = "#FFD700"

SIZES = {
    "icon-192.png":          (192, 192, False),
    "icon-512.png":          (512, 512, False),
    "icon-maskable-192.png": (192, 192, True),
    "icon-maskable-512.png": (512, 512, True),
    "apple-touch-icon.png":  (180, 180, False),
}


def find_font(size):
    """বড় সাইজের font খুঁজে বের করো"""
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_icon(size, maskable=False):
    """একটা icon তৈরি করো - বক্স শেপ"""
    w, h = size
    padding = int(w * 0.12) if maskable else 0
    canvas = w

    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # বক্স ব্যাকগ্রাউন্ড (রাউন্ডেড কর্নার)
    radius = int(canvas * 0.18)
    box = [padding, padding, canvas - padding, canvas - padding]
    draw.rounded_rectangle(box, radius=radius, fill=BG_COLOR)

    # KBA টেক্সট
    font_size = int(canvas * 0.30)
    font = find_font(font_size)
    bbox = draw.textbbox((0, 0), "KBA", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (canvas - tw) // 2
    y = (canvas - th) // 2
    draw.text((x, y), "KBA", fill=TEXT_COLOR, font=font)

    return img


def main():
    print("Generating KBA icons...")
    for filename, (w, h, maskable) in SIZES.items():
        img = create_icon((w, h), maskable)
        path = os.path.join(OUTPUT_DIR, filename)
        img.save(path, "PNG")
        print(f"  OK {filename} ({w}x{h})")

    print(f"\nAll icons generated: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
