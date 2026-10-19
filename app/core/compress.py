"""PDF compression: Ghostscript rebuild + pikepdf cleanup.

Pipeline
  1. Ghostscript rewrites the PDF, downsampling images above the target DPI,
     deduplicating repeated images and subsetting fonts. Text stays selectable.
  2. pikepdf re-saves with object streams (and optionally strips metadata).
  3. If the result isn't smaller, the original is kept (unless told otherwise).
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pikepdf

from .ghostscript import run_ghostscript

# Label -> image DPI. Order matters: it's the order shown in the UI.
PRESETS: dict[str, int] = {
    "Smallest": 72,
    "Balanced": 150,
    "Sharp": 220,
    "Print": 300,
}
DEFAULT_PRESET = "Balanced"
DPI_MIN, DPI_MAX = 50, 400


@dataclass
class CompressOptions:
    dpi: int = PRESETS[DEFAULT_PRESET]
    grayscale: bool = False
    strip_metadata: bool = True
    keep_if_larger: bool = True


@dataclass
class CompressResult:
    source: Path
    output: Path | None
    original_size: int
    new_size: int
    kept_original: bool = False

    @property
    def saved_ratio(self) -> float:
        if not self.original_size:
            return 0.0
        return max(0.0, 1 - self.new_size / self.original_size)


def _pdfsettings_for(dpi: int) -> str:
    # Base profile sets JPEG quality; we then override the resolutions explicitly.
    if dpi <= 96:
        return "/screen"
    if dpi <= 170:
        return "/ebook"
    return "/printer"


def ghostscript_args(src: Path, dst: Path, opts: CompressOptions) -> list[str]:
    dpi = max(DPI_MIN, min(DPI_MAX, int(opts.dpi)))
    mono_dpi = min(600, max(200, dpi * 2))  # line art / scans stay crisp
    args = [
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.6",
        f"-dPDFSETTINGS={_pdfsettings_for(dpi)}",
        "-dNOPAUSE", "-dBATCH", "-dQUIET", "-dSAFER",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true", "-dSubsetFonts=true", "-dEmbedAllFonts=true",
        "-dDownsampleColorImages=true", "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}", "-dColorImageDownsampleThreshold=1.0",
        "-dDownsampleGrayImages=true", "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={dpi}", "-dGrayImageDownsampleThreshold=1.0",
        "-dDownsampleMonoImages=true", "-dMonoImageDownsampleType=/Subsample",
        f"-dMonoImageResolution={mono_dpi}",
    ]
    if opts.grayscale:
        args += ["-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray"]
    args += [f"-sOutputFile={dst}", str(src)]
    return args


def _finalize(path: Path, strip_metadata: bool) -> None:
    with pikepdf.open(path, allow_overwriting_input=True) as pdf:
        if strip_metadata:
            for key in list(pdf.docinfo.keys()):
                del pdf.docinfo[key]
            if "/Metadata" in pdf.Root:
                del pdf.Root.Metadata
        pdf.remove_unreferenced_resources()
        pdf.save(path, compress_streams=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)


def compress_pdf(src: Path, dst: Path, opts: CompressOptions) -> CompressResult:
    src, dst = Path(src), Path(dst)
    original_size = src.stat().st_size

    with tempfile.TemporaryDirectory(prefix="mjcpdf_") as tmp:
        work = Path(tmp) / "out.pdf"
        run_ghostscript(ghostscript_args(src, work, opts))
        _finalize(work, opts.strip_metadata)
        new_size = work.stat().st_size

        if opts.keep_if_larger and new_size >= original_size:
            return CompressResult(src, None, original_size, original_size, kept_original=True)

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(work), dst)
    return CompressResult(src, dst, original_size, new_size)
