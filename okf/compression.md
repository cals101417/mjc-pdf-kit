# Compression pipeline

`core/compress.py::compress_pdf`

1. **Ghostscript (`pdfwrite`)** rebuilds the PDF into a temp folder:
   - base profile by DPI: ≤96 `/screen`, ≤170 `/ebook`, else `/printer` (sets JPEG quality)
   - explicit color/gray image resolution = chosen DPI, bicubic, threshold 1.0 (anything above target is resampled)
   - mono (scanned line art) resolution = 2× DPI, clamped 200–600, so text scans stay readable
   - duplicate image detection, font subsetting/compression
   - grayscale: `ColorConversionStrategy=Gray`
2. **pikepdf** reopens the result: optional metadata strip (Info dict + XMP), unreferenced resources removed, saved with object streams.
3. If the result isn't smaller and "skip files that won't shrink" is on, nothing is written and the row says "Already small".

## Presets
| Name | DPI | Use |
|---|---|---|
| Smallest | 72 | email/upload limits |
| Balanced | 150 | default |
| Sharp | 220 | photos, detailed scans |
| Print | 300 | near-original |
Custom slider: 50–400 in steps of 5.

## Ghostscript lookup (`core/ghostscript.py`)
`MJC_GHOSTSCRIPT` env → bundled `ghostscript/bin` → PATH → `Program Files\gs\gs*\bin` (newest version).

## Measured
Synthetic 300-DPI photo pages at Balanced: 13.6 MB → 2.4 MB (−83%). Real-world savings vary a lot; text-only PDFs often shrink little.

## Not yet (vs. the original MinimalPDF)
Per-image recompression (pngquant/oxipng/jbig2), true lossless mode, PDF/A, linearization.
