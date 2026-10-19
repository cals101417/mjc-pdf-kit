# Log

- **2026-10-19** — v0.1.0 scaffolded. Core (compress, merge, split, rotate, delete, range parser) with 15 passing tests. Branded CustomTkinter UI with drag and drop, background worker, saved settings. Verified every tool through the UI on Linux/Xvfb; compression 13.6 MB → 2.4 MB on synthetic scans. PyInstaller spec + build.bat added; Windows build not yet run.
- **2026-10-19** — First Windows run. Installed Ghostscript 10.08.0 (C:\Program Files\gs). The compression test now uses `find_ghostscript()` for its skip check, so it no longer skips when Ghostscript is installed in Program Files but missing from PATH. 15/15 pass on Windows.
- **2026-10-19** — First Windows build: `dist\MJC PDF Kit.exe` (~27 MB, PyInstaller one-file). Launches fine. Ghostscript not bundled, so each PC needs it installed.
