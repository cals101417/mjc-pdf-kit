# Decisions

- **2026-10-19 — Desktop .exe, Python + CustomTkinter.** Michael chose a Windows desktop app over a browser app. CustomTkinter keeps the original's Python approach but gives a modern look with far less custom widget code than raw Tkinter.
- **2026-10-19 — Rewrite, not fork.** The original is AGPL-3.0. Writing our own code keeps licensing choices open; only Ghostscript (if bundled) carries AGPL.
- **2026-10-19 — v0.1 scope = core set.** Compress, Merge, Split/Extract, Rotate, Delete. Watermark, header/footer, password, metadata editor, PDF→image, repair deferred (see roadmap).
- **2026-10-19 — Ghostscript not bundled by default.** Smaller exe, no AGPL obligations by default; bundling supported via `./ghostscript`.
- **2026-10-19 — Branding from mcalignerdev.com.** Navy #0B0F19, gold #D39A1A, periwinkle #6E8CFF.
