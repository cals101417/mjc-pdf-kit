# Roadmap

Ordered by value to Michael's own workflow and to the portfolio story.

1. **Target size** — "Compress to under 10 MB": try presets from Print down until it fits. Solves the real email/upload problem better than DPI numbers.
2. **Page thumbnails** in Split/Rotate/Delete (render with Ghostscript `png16m` at low DPI) so users click pages instead of typing ranges.
3. **Watermark / stamp** (text + logo, opacity, position) — useful for client drafts.
4. **Password protect / remove password** (pikepdf encryption).
5. **PDF → images** (Ghostscript png/jpeg devices).
6. **Image-level optimization** (pngquant, jbig2) for bigger savings on scans.
7. Right-click "Compress with MJC PDF Kit" in Explorer (registry entry via installer).
8. Installer (Inno Setup) + auto-update check against GitHub releases.
