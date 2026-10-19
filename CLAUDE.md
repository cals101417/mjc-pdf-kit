# CLAUDE.md

Windows desktop PDF toolkit (compress, merge, split, rotate, delete) in Python + CustomTkinter, branded for mcalignerdev.com.

## Before you change anything
- Read `okf/index.md` and follow links only to the concepts your change touches. Append to `okf/log.md` after meaningful changes; never rewrite it.
- Keep `app/core/` free of UI imports. UI goes in `app/ui/`.
- Never overwrite a user's original PDF. New outputs go through `core.files.unique_path`.
- Long work runs through `ui.worker.Worker`; never touch widgets from a worker thread (use `worker.post`).
- Error messages are shown to end users verbatim: plain English, say what to do next.

## Commands
- Run from source: `run.bat` (or `python run.py`)
- Tests: `python -m pytest -q`
- Build exe: `build.bat` → `dist\MJC PDF Kit.exe`

## Brand
Colors and fonts live only in `app/ui/theme.py`. Name/links only in `app/config.py`.
