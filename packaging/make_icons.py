"""Gera assets/icon.png e assets/icon.ico (rodar da raiz: `python packaging/make_icons.py`)."""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
BG = (28, 28, 30)
BRAND = (217, 119, 87)
GREEN = (48, 209, 88)
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def draw() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((32, 32, SIZE - 32, SIZE - 32), radius=220, fill=BG)
    pad, width = 210, 120
    bounds = (pad, pad, SIZE - pad, SIZE - pad)
    d.arc(bounds, 40, 320, fill=BRAND, width=width)  # o "C"
    r = 70
    cx, cy = SIZE / 2, SIZE / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GREEN)
    return img


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    big = draw()
    big.resize((256, 256), Image.LANCZOS).save(ASSETS / "icon.png")
    big.resize((256, 256), Image.LANCZOS).save(
        ASSETS / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print("ok:", ASSETS)
