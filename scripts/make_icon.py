"""Draws assets/app.ico and assets/icon.png in brand colors. Re-run after tweaking."""
from pathlib import Path
from PIL import Image, ImageDraw

GOLD, NAVY = (211, 154, 26, 255), (11, 15, 25, 255)
OUT = Path(__file__).resolve().parents[1] / "assets"


def draw(size: int = 512) -> Image.Image:
    s = size / 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(112 * s), fill=GOLD)
    # document with folded corner
    x0, y0, x1, y1, fold = 150 * s, 92 * s, 362 * s, 420 * s, 70 * s
    d.polygon([(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)], fill=NAVY)
    d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=(255, 214, 120, 255))
    # squeeze arrows (pointing inward)
    cx, w = 256 * s, 22 * s
    for top, direction in ((176 * s, 1), (336 * s, -1)):
        tip = top + direction * 50 * s
        d.polygon([(cx - 38 * s, top), (cx + 38 * s, top), (cx, tip)], fill=GOLD)
    d.rounded_rectangle([x0 + 40 * s, 246 * s, x1 - 40 * s, 266 * s], radius=int(10 * s), fill=GOLD)
    return img


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    big = draw(512)
    big.save(OUT / "icon.png")
    big.save(OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", OUT / "app.ico")
