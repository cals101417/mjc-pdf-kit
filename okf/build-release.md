# Build & release

- `build.bat` creates `.venv`, installs `requirements.txt` + PyInstaller, runs `mjc-pdf-kit.spec`.
- Output: one-file windowed exe `dist\MJC PDF Kit.exe` with `assets/`, CustomTkinter themes and the tkdnd library bundled.
- The exe must be built on Windows (PyInstaller doesn't cross-compile). The spec was verified with a Linux build.
- Unsigned exes trigger Windows SmartScreen ("More info → Run anyway"). Code signing removes it; costs money, skip until public release.

## Ghostscript
- Default: not bundled. App detects an installed copy and shows "Ghostscript missing" + download link otherwise.
- Bundled: place `bin` + `lib` under `./ghostscript/`; the spec includes it automatically.
- Ghostscript is AGPL-3.0. Bundling means distributing it under AGPL terms (license text + source offer). Decide before public distribution.
