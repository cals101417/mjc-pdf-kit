"""Merge: combine several PDFs into one, in the order shown."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from .. import theme as t
from ..widgets import DropZone, ask_save_pdf, ghost_button, icon_button, primary_button, section_label
from .base import ToolView
from ...core import pages
from ...core.files import human_size


class MergeRow(ctk.CTkFrame):
    def __init__(self, master, view: "MergeView", path: Path, count: int):
        super().__init__(master, fg_color=t.SURFACE_2, corner_radius=10)
        self.path, self.count = path, count
        self.grid_columnconfigure(1, weight=1)
        self.number = ctk.CTkLabel(self, text="", width=30, font=t.mono(12), text_color=t.GOLD)
        self.number.grid(row=0, column=0, rowspan=2, padx=(12, 6), pady=10)
        name = path.name if len(path.name) < 56 else path.name[:53] + "…"
        ctk.CTkLabel(self, text=name, font=t.font(13, "bold"), text_color=t.TEXT,
                     anchor="w").grid(row=0, column=1, sticky="sw", pady=(10, 0))
        noun = "page" if count == 1 else "pages"
        ctk.CTkLabel(self, text=f"{count} {noun}  ·  {human_size(path.stat().st_size)}",
                     font=t.mono(11), text_color=t.MUTED, anchor="w").grid(
            row=1, column=1, sticky="nw", pady=(0, 10))
        for col, (glyph, step) in enumerate([("↑", -1), ("↓", 1)], start=2):
            icon_button(self, glyph, lambda s=step: view.move(self, s)).grid(row=0, column=col, rowspan=2)
        icon_button(self, "✕", lambda: view.remove(self)).grid(row=0, column=4, rowspan=2, padx=(0, 10))


class MergeView(ToolView):
    title = "Merge PDFs"
    subtitle = "Combine files into one PDF. Use the arrows to set the order."

    def build(self) -> None:
        self.rows: list[MergeRow] = []
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(2, weight=1)
        DropZone(self.body, self.settings, self.add, height=112).grid(row=0, column=0, sticky="ew")

        head = ctk.CTkFrame(self.body, fg_color="transparent")
        head.grid(row=1, column=0, sticky="ew", pady=(16, 8))
        head.grid_columnconfigure(0, weight=1)
        self.count_label = section_label(head, "Add at least two PDFs")
        self.count_label.grid(row=0, column=0, sticky="w")
        self.clear_btn = ghost_button(head, "Clear", self.clear, width=64)

        self.list = ctk.CTkScrollableFrame(self.body, fg_color="transparent",
                                           scrollbar_button_color=t.BORDER_STRONG)
        self.list.grid(row=2, column=0, sticky="nsew")
        self.list.grid_columnconfigure(0, weight=1)

        self.go = primary_button(self.footer, "Merge", self.start, width=180)
        self.go.grid(row=0, column=2, padx=(16, 0))
        self._refresh()

    def add(self, paths: list[Path]) -> None:
        for p in paths:
            try:
                count = pages.page_count(p)
            except Exception as exc:
                self.status.show(str(exc), "error")
                continue
            self.rows.append(MergeRow(self.list, self, p, count))
        self._refresh()

    def move(self, row: MergeRow, step: int) -> None:
        i = self.rows.index(row)
        j = i + step
        if 0 <= j < len(self.rows):
            self.rows[i], self.rows[j] = self.rows[j], self.rows[i]
            self._refresh()

    def remove(self, row: MergeRow) -> None:
        self.rows.remove(row)
        row.destroy()
        self._refresh()

    def clear(self) -> None:
        for r in self.rows:
            r.destroy()
        self.rows.clear()
        self._refresh()

    def _refresh(self) -> None:
        for i, r in enumerate(self.rows):
            r.number.configure(text=f"{i + 1:02d}")
            r.grid(row=i, column=0, sticky="ew", pady=4)
        n = len(self.rows)
        total = sum(r.count for r in self.rows)
        if n:
            self.count_label.configure(text=f"{n} files  ·  {total} pages total" if n > 1
                                       else "1 file  ·  add one more")
            self.clear_btn.grid(row=0, column=1)
        else:
            self.count_label.configure(text="Add at least two PDFs")
            self.clear_btn.grid_remove()
        self.go.set_enabled(n >= 2, f"Merge {n} PDFs" if n >= 2 else "Merge")

    def start(self) -> None:
        if len(self.rows) < 2 or self.worker.busy:
            return
        sources = [r.path for r in self.rows]
        dst = ask_save_pdf(self.settings, f"{sources[0].stem}_merged.pdf")
        if not dst or any(self.same_as_source(s, dst) for s in sources):
            return
        self.set_busy(True, f"Merging {len(sources)} files…")
        self.worker.run(lambda: pages.merge(sources, dst), self._done, self._failed)

    def _done(self, out: Path) -> None:
        self.set_busy(False)
        total = sum(r.count for r in self.rows)
        self.status.show(f"Merged into {out.name}  ·  {total} pages, {human_size(out.stat().st_size)}",
                         "ok", reveal=out)

    def _failed(self, message: str) -> None:
        self.set_busy(False)
        self.status.show(message, "error")
