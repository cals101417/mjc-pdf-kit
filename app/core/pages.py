"""Page tools built on pikepdf: merge, split/extract, rotate, delete."""

from __future__ import annotations

from pathlib import Path

import pikepdf

from .files import unique_path
from .ranges import RangeError, pages_in, parse_ranges


def _open(path: Path) -> pikepdf.Pdf:
    try:
        return pikepdf.open(path)
    except pikepdf.PasswordError:
        raise RuntimeError(f"{Path(path).name} is password-protected. Remove the password first.")
    except pikepdf.PdfError as exc:
        raise RuntimeError(f"{Path(path).name} couldn't be opened as a PDF ({exc}).")


def page_count(path: Path) -> int:
    with _open(path) as pdf:
        return len(pdf.pages)


def _save(pdf: pikepdf.Pdf, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(dst, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return dst


def merge(sources: list[Path], dst: Path) -> Path:
    if len(sources) < 2:
        raise RuntimeError("Add at least two PDFs to merge.")
    out = pikepdf.new()
    for src in sources:
        with _open(src) as pdf:
            out.pages.extend(pdf.pages)
    return _save(out, Path(dst))


def split(src: Path, out_dir: Path, mode: str, every: int = 1,
          ranges_text: str = "", single_file: bool = False) -> list[Path]:
    """mode: "every" (chunks of `every` pages) or "ranges" (custom ranges)."""
    src, out_dir = Path(src), Path(out_dir)
    stem = src.stem
    outputs: list[Path] = []
    with _open(src) as pdf:
        total = len(pdf.pages)
        if mode == "every":
            if every < 1:
                raise RangeError("Pages per file must be 1 or more.")
            groups = [(s, min(s + every - 1, total)) for s in range(1, total + 1, every)]
        else:
            groups = parse_ranges(ranges_text, total)

        if single_file:
            out = pikepdf.new()
            for start, end in groups:
                for n in range(start, end + 1):
                    out.pages.append(pdf.pages[n - 1])
            label = ranges_text.replace(" ", "") if mode == "ranges" else "extract"
            outputs.append(_save(out, unique_path(out_dir, f"{stem}_pages {label}")))
            return outputs

        for start, end in groups:
            out = pikepdf.new()
            for n in range(start, end + 1):
                out.pages.append(pdf.pages[n - 1])
            label = f"p{start}" if start == end else f"p{start}-{end}"
            outputs.append(_save(out, unique_path(out_dir, f"{stem}_{label}")))
    return outputs


def rotate(src: Path, dst: Path, angle: int, ranges_text: str = "") -> Path:
    if angle not in (90, 180, 270):
        raise ValueError("Angle must be 90, 180 or 270.")
    with _open(src) as pdf:
        total = len(pdf.pages)
        targets = pages_in(parse_ranges(ranges_text, total)) if ranges_text.strip() \
            else set(range(1, total + 1))
        for n in sorted(targets):
            pdf.pages[n - 1].rotate(angle, relative=True)
        return _save(pdf, Path(dst))


def delete_pages(src: Path, dst: Path, ranges_text: str) -> Path:
    with _open(src) as pdf:
        total = len(pdf.pages)
        doomed = pages_in(parse_ranges(ranges_text, total))
        if len(doomed) >= total:
            raise RangeError("That would delete every page. Leave at least one.")
        for n in sorted(doomed, reverse=True):
            del pdf.pages[n - 1]
        return _save(pdf, Path(dst))
