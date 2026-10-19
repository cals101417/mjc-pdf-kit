"""Compress: batch-shrink PDFs with quality presets or a custom DPI."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from .. import theme as t
from ..widgets import (DropZone, card, ghost_button, hint, icon_button, primary_button,
                       section_label, segmented, switch, ask_folder)
from .base import ToolView
from ...config import COMPRESSED_SUFFIX
from ...core.compress import DPI_MAX, DPI_MIN, PRESETS, CompressOptions, compress_pdf
from ...core.files import human_size, unique_path

PRESET_NOTES = {
    "Smallest": "For email and uploads with size limits. Photos get soft.",
    "Balanced": "Good for most files. Text stays sharp, photos look fine on screen.",
    "Sharp": "Crisp images and scans, still a solid size cut.",
    "Print": "Close to the original. Smallest savings.",
    "Custom": "Your own image resolution. Lower DPI = smaller file.",
}


class FileRow(ctk.CTkFrame):
    def __init__(self, master, path: Path, on_remove):
        super().__init__(master, fg_color=t.SURFACE_2, corner_radius=10)
        self.path = path
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="PDF", width=34, height=34, corner_radius=7, fg_color=t.GOLD_SOFT,
                     text_color=t.GOLD, font=t.font(10, "bold")).grid(row=0, column=0, rowspan=2,
                                                                       padx=(12, 12), pady=10)
        name = path.name if len(path.name) < 48 else path.name[:45] + "…"
        ctk.CTkLabel(self, text=name, font=t.font(13, "bold"), text_color=t.TEXT,
                     anchor="w").grid(row=0, column=1, sticky="sw", pady=(10, 0))
        self.meta = ctk.CTkLabel(self, text=human_size(path.stat().st_size), font=t.mono(11),
                                 text_color=t.MUTED, anchor="w")
        self.meta.grid(row=1, column=1, sticky="nw", pady=(0, 10))
        self.result = ctk.CTkLabel(self, text="", font=t.font(13, "bold"), text_color=t.MUTED)
        self.result.grid(row=0, column=2, rowspan=2, padx=8)
        self.remove = icon_button(self, "✕", lambda: on_remove(self))
        self.remove.grid(row=0, column=3, rowspan=2, padx=(0, 10))

    def set_state(self, kind: str, text: str = "", meta: str | None = None) -> None:
        colors = {"working": t.BLUE, "done": t.GOLD, "kept": t.MUTED, "error": t.DANGER}
        self.result.configure(text=text, text_color=colors.get(kind, t.MUTED))
        if meta is not None:
            self.meta.configure(text=meta)


class CompressView(ToolView):
    title = "Compress PDF"
    subtitle = "Shrink PDFs for email and uploads. Text stays selectable; everything runs offline."

    def build(self) -> None:
        self.rows: list[FileRow] = []
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)

        # Left: files
        DropZone(self.body, self.settings, self.add_files).grid(row=0, column=0, sticky="ew")
        list_head = ctk.CTkFrame(self.body, fg_color="transparent")
        list_head.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        list_head.grid_columnconfigure(0, weight=1)
        list_head.grid_rowconfigure(1, weight=1)
        self.count_label = section_label(list_head, "No files yet")
        self.count_label.grid(row=0, column=0, sticky="w")
        self.clear_btn = ghost_button(list_head, "Clear", self.clear, width=64)
        self.list = ctk.CTkScrollableFrame(list_head, fg_color="transparent",
                                           scrollbar_button_color=t.BORDER_STRONG,
                                           scrollbar_button_hover_color=t.FAINT)
        self.list.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        self.list.grid_columnconfigure(0, weight=1)
        self.empty = ctk.CTkLabel(self.list, text="Your files will show up here, with the\n"
                                  "before and after size of each one.",
                                  font=t.font(13), text_color=t.FAINT, justify="center")

        # Right: options
        panel = card(self.body, width=300)
        panel.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(20, 0))
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        pad = {"padx": 20, "sticky": "ew"}

        section_label(panel, "Quality").grid(row=0, column=0, pady=(20, 8), **pad)
        self.preset = segmented(panel, list(PRESETS), command=self._preset_picked)
        self.preset.grid(row=1, column=0, **pad)

        dpi_row = ctk.CTkFrame(panel, fg_color="transparent")
        dpi_row.grid(row=2, column=0, pady=(14, 0), **pad)
        dpi_row.grid_columnconfigure(0, weight=1)
        hint(dpi_row, "Image resolution").grid(row=0, column=0, sticky="w")
        self.dpi_label = ctk.CTkLabel(dpi_row, text="", font=t.mono(12), text_color=t.GOLD)
        self.dpi_label.grid(row=0, column=1, sticky="e")
        self.dpi = ctk.CTkSlider(panel, from_=DPI_MIN, to=DPI_MAX, number_of_steps=(DPI_MAX - DPI_MIN) // 5,
                                 command=self._dpi_moved, progress_color=t.GOLD, button_color=t.GOLD,
                                 button_hover_color=t.GOLD_HOVER, fg_color=t.BORDER_STRONG, height=16)
        self.dpi.grid(row=3, column=0, pady=(4, 0), **pad)
        self.note = hint(panel, "", wraplength=258)
        self.note.grid(row=4, column=0, pady=(8, 0), **pad)

        section_label(panel, "Options").grid(row=5, column=0, pady=(22, 6), **pad)
        self.gray = ctk.BooleanVar(value=self.settings["grayscale"])
        self.strip = ctk.BooleanVar(value=self.settings["strip_metadata"])
        self.keep = ctk.BooleanVar(value=self.settings["keep_if_larger"])
        for i, (label, var) in enumerate([("Convert to grayscale", self.gray),
                                          ("Remove hidden metadata", self.strip),
                                          ("Skip files that won't shrink", self.keep)]):
            switch(panel, label, var, command=self._remember).grid(row=6 + i, column=0, pady=5, **pad)

        section_label(panel, "Save to").grid(row=9, column=0, pady=(20, 6), **pad)
        out_row = ctk.CTkFrame(panel, fg_color="transparent")
        out_row.grid(row=10, column=0, **pad)
        out_row.grid_columnconfigure(0, weight=1)
        self.out_label = hint(out_row, "", wraplength=170)
        self.out_label.grid(row=0, column=0, sticky="w")
        ghost_button(out_row, "Change", self._pick_folder, width=70).grid(row=0, column=1)
        self.reset_out = ctk.CTkButton(panel, text="Use original's folder", command=self._reset_folder,
                                       fg_color="transparent", hover_color=t.SURFACE_2, height=22,
                                       text_color=t.BLUE, font=t.font(12), anchor="w")

        panel.grid_rowconfigure(12, weight=1)
        self.go = primary_button(panel, "Compress", self.start)
        self.go.grid(row=13, column=0, padx=20, pady=20, sticky="ew")

        # Restore last choices
        preset = self.settings.get("preset", "Balanced")
        dpi = int(self.settings.get("dpi", PRESETS.get(preset, 150)))
        self.dpi.set(dpi)
        if preset in PRESETS:
            self.preset.set(preset)
        self._sync_dpi(dpi, preset if preset in PRESETS else "Custom")
        self._show_folder()
        self._refresh()

    # ----- options -----
    def _preset_picked(self, name: str) -> None:
        self.dpi.set(PRESETS[name])
        self._sync_dpi(PRESETS[name], name)

    def _dpi_moved(self, value: float) -> None:
        dpi = int(round(value / 5) * 5)
        match = next((n for n, d in PRESETS.items() if d == dpi), None)
        self.preset.set(match or "")
        self._sync_dpi(dpi, match or "Custom")

    def _sync_dpi(self, dpi: int, preset: str) -> None:
        self.dpi_label.configure(text=f"{dpi} DPI")
        self.note.configure(text=PRESET_NOTES[preset])
        self.settings["dpi"], self.settings["preset"] = dpi, preset
        self._remember()

    def _remember(self) -> None:
        self.settings.update(grayscale=self.gray.get(), strip_metadata=self.strip.get(),
                             keep_if_larger=self.keep.get())
        self.settings.save()

    def _pick_folder(self) -> None:
        folder = ask_folder(self.settings)
        if folder:
            self.settings["output_folder"] = str(folder)
            self._show_folder()
            self._remember()

    def _reset_folder(self) -> None:
        self.settings["output_folder"] = ""
        self._show_folder()
        self._remember()

    def _show_folder(self) -> None:
        folder = self.settings.get("output_folder")
        if folder:
            shown = folder if len(folder) < 34 else "…" + folder[-33:]
            self.out_label.configure(text=shown, text_color=t.TEXT)
            self.reset_out.grid(row=11, column=0, padx=14, pady=(4, 0), sticky="w")
        else:
            self.out_label.configure(text=f"Next to each original,\nnamed …{COMPRESSED_SUFFIX}.pdf",
                                     text_color=t.MUTED)
            self.reset_out.grid_remove()

    # ----- file list -----
    def add_files(self, paths: list[Path]) -> None:
        known = {r.path.resolve() for r in self.rows}
        for p in paths:
            if p.resolve() not in known and p.is_file():
                row = FileRow(self.list, p, self.remove_row)
                row.grid(row=len(self.rows), column=0, sticky="ew", pady=4)
                self.rows.append(row)
                known.add(p.resolve())
        self._refresh()
        self.status.show("")

    def remove_row(self, row: FileRow) -> None:
        if self.worker.busy:
            return
        self.rows.remove(row)
        row.destroy()
        for i, r in enumerate(self.rows):
            r.grid(row=i)
        self._refresh()

    def clear(self) -> None:
        if self.worker.busy:
            return
        for r in self.rows:
            r.destroy()
        self.rows.clear()
        self._refresh()
        self.status.show("")

    def _refresh(self) -> None:
        n = len(self.rows)
        if n:
            total = sum(r.path.stat().st_size for r in self.rows if r.path.exists())
            self.count_label.configure(text=f"{n} file{'s' * (n != 1)}  ·  {human_size(total)}")
            self.clear_btn.grid(row=0, column=1, sticky="e")
        else:
            self.count_label.configure(text="No files yet")
            self.clear_btn.grid_remove()
        self.go.set_enabled(bool(n), f"Compress {n} file{'s' * (n != 1)}" if n else "Compress")
        if n:
            self.empty.grid_remove()
        else:
            self.empty.grid(row=0, column=0, sticky="ew", pady=40)

    # ----- run -----
    def start(self) -> None:
        if not self.rows or self.worker.busy:
            return
        if not self.app.ghostscript:
            self.status.show("Ghostscript isn't installed yet. Install it from ghostscript.com, "
                             "then restart the app.", "error")
            return
        opts = CompressOptions(dpi=int(self.settings["dpi"]), grayscale=self.gray.get(),
                               strip_metadata=self.strip.get(), keep_if_larger=self.keep.get())
        out_folder = self.settings.get("output_folder")
        rows = list(self.rows)
        for r in rows:
            r.set_state("idle", "", human_size(r.path.stat().st_size))

        def job():
            totals = {"before": 0, "after": 0, "done": 0, "kept": 0, "failed": 0, "last": None}
            for row in rows:
                self.worker.post(row.set_state, "working", "Working…")
                folder = Path(out_folder) if out_folder else row.path.parent
                dst = unique_path(folder, row.path.stem + COMPRESSED_SUFFIX)
                try:
                    res = compress_pdf(row.path, dst, opts)
                except Exception as exc:
                    totals["failed"] += 1
                    self.worker.post(row.set_state, "error", "Failed", str(exc)[:90])
                    continue
                totals["before"] += res.original_size
                totals["after"] += res.new_size
                if res.kept_original:
                    totals["kept"] += 1
                    self.worker.post(row.set_state, "kept", "Already small",
                                     f"{human_size(res.original_size)}  ·  left as is")
                else:
                    totals["done"] += 1
                    totals["last"] = res.output
                    self.worker.post(row.set_state, "done", f"−{res.saved_ratio:.0%}",
                                     f"{human_size(res.original_size)}  →  {human_size(res.new_size)}")
            return totals

        self.set_busy(True, f"Compressing {len(rows)} file{'s' * (len(rows) != 1)}…")
        self.go.set_enabled(False)
        self.worker.run(job, self._finished, self._failed)

    def _finished(self, s: dict) -> None:
        self.set_busy(False)
        self._refresh()
        if not s["done"]:
            if s["failed"]:
                self.status.show("Nothing was compressed. See the red notes on each file.", "error")
            else:
                self.status.show("These files are already well optimized, so they were left as is.", "warn")
            return
        saved = s["before"] - s["after"]
        pct = saved / s["before"] if s["before"] else 0
        msg = (f"Saved {human_size(saved)} ({pct:.0%}).  "
               f"{human_size(s['before'])} → {human_size(s['after'])}")
        extra = []
        if s["kept"]:
            extra.append(f"{s['kept']} already small")
        if s["failed"]:
            extra.append(f"{s['failed']} failed")
        if extra:
            msg += "  ·  " + ", ".join(extra)
        self.status.show(msg, "warn" if s["failed"] else "ok", reveal=s["last"])

    def _failed(self, message: str) -> None:
        self.set_busy(False)
        self._refresh()
        self.status.show(message, "error")
