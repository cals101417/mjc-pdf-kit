import sys
from pathlib import Path

import pikepdf
import pytest
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _photo(seed: int, size=(2480, 3508)) -> Image.Image:
    """A photo-like A4 page at 300 DPI: gradients + soft noise, so JPEG can't cheat."""
    img = Image.effect_noise(size, 60 + seed).convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(2))
    draw = ImageDraw.Draw(img)
    for i in range(0, size[1], 40):
        draw.rectangle([0, i, size[0], i + 20], fill=((i * 3 + seed * 40) % 255, 120, 200 - i % 200))
    return img.filter(ImageFilter.GaussianBlur(1))


@pytest.fixture
def scanned_pdf(tmp_path) -> Path:
    path = tmp_path / "scan.pdf"
    pages = [_photo(i) for i in range(3)]
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=300, quality=92)
    return path


@pytest.fixture
def ten_pages(tmp_path) -> Path:
    path = tmp_path / "ten.pdf"
    pdf = pikepdf.new()
    for i in range(10):
        pdf.add_blank_page(page_size=(612 + i, 792))  # width encodes the page index
    pdf.save(path)
    return path


def page_widths(path: Path) -> list[int]:
    with pikepdf.open(path) as pdf:
        return [int(p.mediabox[2]) - 612 for p in pdf.pages]
