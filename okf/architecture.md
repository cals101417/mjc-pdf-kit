# Architecture

```
run.py → app.main → ui.window.App
                     ├─ sidebar (nav, engine status, site link)
                     └─ stage → one ToolView at a time (created lazily on first visit)
ToolView (ui/views/base.py)
  header · body (tool-specific) · footer (StatusLine, progress bar, primary action)
  └─ calls app.core.* inside Worker.run(job, on_done, on_error)
```

## Layers
- `app/core/` — pure PDF logic. No tkinter. Raises exceptions with user-readable messages (`RangeError`, `RuntimeError`, `GhostscriptMissing`).
- `app/ui/` — CustomTkinter. Views own their state; the window owns navigation, settings and the worker.
- `app/settings.py` — JSON in `%APPDATA%\MJC PDF Kit\settings.json` (XDG on Linux). Failures are ignored.

## Threading
`Worker` runs one job at a time on a daemon thread. Results come back through a queue polled every 80 ms on the Tk thread. Worker code calls `worker.post(fn, *args)` for live updates (Compress uses this for per-file results). Navigation is disabled while busy.

## Safety rules
- Outputs never replace inputs: `unique_path` adds ` (2)`, ` (3)`; save dialogs reject the source path.
- Password-protected and broken PDFs surface a plain message instead of a traceback.

## Drag and drop
`tkinterdnd2` is loaded on the root window (`TkinterDnD._require`). If that fails, `widgets.DND_READY` stays false and drop zones become click-to-browse with matching copy.
