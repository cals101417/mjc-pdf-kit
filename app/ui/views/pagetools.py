"""Single-file page tools: Split / Extract, Rotate, Delete pages."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from .. import theme as t
from ..widgets import (ask_folder, ask_save_pdf, card, entry, ghost_button, hint, primary_button,
                       section_label, segmented, switch)
from .base import SingleFileField, ToolView
from ...core import pages
from ...core.files import human_size


class _PageToolView(ToolView):
    action_text = "Run"

    def build(self) -> None:
        self.body.grid_columnconfigure(0, weight=1)
        self.file = SingleFileField(self.body, self, on_change=self._file_changed)
        self.file.grid(row=0, column=0, sticky="ew")
        self.options = card(self.body)
        self.options.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self.options.grid_columnconfigure(0, weight=1)
        self.build_options(self.options)
        self.go = primary_button(self.footer, self.action_text, self.start, width=180)
        self.go.grid(row=0, column=2, padx=(16, 0))
        self.go.set_enabled(False)

    def build_options(self, frame) -> None:
        raise NotImplementedError

    def _file_changed(self) -> None:
        self.go.set_enabled(True)
        self.on_file()

    def on_file(self) -> None:
        pass

    def _failed(self, message: str) -> None:
        self.set_busy(False)
        self.status.show(message, "error")

    def _range_row(self, frame, row: int, label: str, placeholder: str,
                   bottom: int = 0) -> ctk.CTkEntry:
        section_label(frame, label).grid(row=row, column=0, padx=22, pady=(18, 6), sticky="w")
        field = entry(frame, placeholder, width=360)
        field.grid(row=row + 1, column=0, padx=22, sticky="w")
        hint(frame, "Commas between items. Use “end” for the last page, e.g. 1-3, 7, 10-end").grid(
            row=row + 2, column=0, padx=22, pady=(6, bottom), sticky="w")
        return field


class SplitView(_PageToolView):
    title = "Split & extract"
    subtitle = "Break a PDF into smaller files, or pull out just the pages you need."
    action_text = "Split PDF"
    MODES = ["Every page", "Every N pages", "Custom ranges"]

    def build_options(self, f) -> None:
        section_label(f, "How to split").grid(row=0, column=0, padx=22, pady=(20, 8), sticky="w")
        self.mode = segmented(f, self.MODES, command=lambda _v: self._mode_changed())
        self.mode.grid(row=1, column=0, padx=22, sticky="w")
        self.mode.set("Every page")

        self.n_frame = ctk.CTkFrame(f, fg_color="transparent")
        hint(self.n_frame, "Pages per file").grid(row=0, column=0, padx=(0, 10))
        self.n = entry(self.n_frame, "e.g. 5", width=90)
        self.n.grid(row=0, column=1)

        self.r_frame = ctk.CTkFrame(f, fg_color="transparent")
        self.ranges = entry(self.r_frame, "1-3, 5, 9-end", width=360)
        self.ranges.grid(row=0, column=0, sticky="w")
        hint(self.r_frame, "Each range becomes its own file.").grid(row=1, column=0, pady=(6, 0), sticky="w")
        self.one_file = ctk.BooleanVar(value=False)
        switch(self.r_frame, "Put all of them in one file instead (extract)", self.one_file).grid(
            row=2, column=0, pady=(12, 0), sticky="w")

        self.preview = hint(f, "")
        self.preview.grid(row=4, column=0, padx=22, pady=(14, 0), sticky="w")

        out = ctk.CTkFrame(f, fg_color="transparent")
        out.grid(row=5, column=0, padx=22, pady=(14, 20), sticky="ew")
        out.grid_columnconfigure(0, weight=1)
        self.out_folder: Path | None = None
        self.out_label = hint(out, "Saves next to the original")
        self.out_label.grid(row=0, column=0, sticky="w")
        ghost_button(out, "Change folder", self._pick_folder, width=120).grid(row=0, column=1)

        self.n.bind("<KeyRelease>", lambda _e: self._update_preview())
        self._mode_changed()

    def _mode_changed(self) -> None:
        mode = self.mode.get()
        self.n_frame.grid_forget()
        self.r_frame.grid_forget()
        if mode == "Every N pages":
            self.n_frame.grid(row=2, column=0, padx=22, pady=(14, 0), sticky="w")
        elif mode == "Custom ranges":
            self.r_frame.grid(row=2, column=0, padx=22, pady=(14, 0), sticky="w")
        self._update_preview()

    def _update_preview(self) -> None:
        total = self.file.pages
        if not total:
            self.preview.configure(text="")
            return
        mode = self.mode.get()
        if mode == "Every page":
            self.preview.configure(text=f"→ {total} files, one page each")
        elif mode == "Every N pages":
            try:
                n = int(self.n.get())
                files = -(-total // n)
                self.preview.configure(text=f"→ {files} file{'s' * (files != 1)} of up to {n} pages")
            except (ValueError, ZeroDivisionError):
                self.preview.configure(text="")
        else:
            self.preview.configure(text="")

    def on_file(self) -> None:
        self._update_preview()

    def _pick_folder(self) -> None:
        folder = ask_folder(self.settings)
        if folder:
            self.out_folder = folder
            shown = str(folder) if len(str(folder)) < 60 else "…" + str(folder)[-59:]
            self.out_label.configure(text=shown, text_color=t.TEXT)

    def start(self) -> None:
        src = self.file.path
        if not src or self.worker.busy:
            return
        mode = self.mode.get()
        folder = self.out_folder or src.parent
        if mode == "Every N pages":
            try:
                every = int(self.n.get())
                assert every >= 1
            except (ValueError, AssertionError):
                self.status.show("Enter how many pages each file should have (1 or more).", "warn")
                return
            job = lambda: pages.split(src, folder, "every", every=every)
        elif mode == "Every page":
            job = lambda: pages.split(src, folder, "every", every=1)
        else:
            text, one = self.ranges.get(), self.one_file.get()
            job = lambda: pages.split(src, folder, "ranges", ranges_text=text, single_file=one)
        self.set_busy(True, "Splitting…")
        self.worker.run(job, self._done, self._failed)

    def _done(self, outs: list[Path]) -> None:
        self.set_busy(False)
        n = len(outs)
        self.status.show(f"Created {n} file{'s' * (n != 1)} in {outs[0].parent.name}", "ok",
                         reveal=outs[0])


class RotateView(_PageToolView):
    title = "Rotate pages"
    subtitle = "Fix sideways or upside-down scans. Rotate every page or just some."
    action_text = "Rotate & save"
    ANGLES = {"↻  90° right": 90, "180°": 180, "↺  90° left": 270}

    def build_options(self, f) -> None:
        section_label(f, "Direction").grid(row=0, column=0, padx=22, pady=(20, 8), sticky="w")
        self.angle = segmented(f, list(self.ANGLES))
        self.angle.grid(row=1, column=0, padx=22, sticky="w")
        self.angle.set("↻  90° right")
        self.pages = self._range_row(f, 2, "Pages", "Leave empty for all pages", bottom=20)

    def start(self) -> None:
        src = self.file.path
        if not src or self.worker.busy:
            return
        dst = ask_save_pdf(self.settings, f"{src.stem}_rotated.pdf")
        if not dst or self.same_as_source(src, dst):
            return
        angle, text = self.ANGLES[self.angle.get()], self.pages.get()
        self.set_busy(True, "Rotating…")
        self.worker.run(lambda: pages.rotate(src, dst, angle, text), self._done, self._failed)

    def _done(self, out: Path) -> None:
        self.set_busy(False)
        which = self.pages.get().strip() or "all pages"
        self.status.show(f"Rotated {which}. Saved as {out.name}", "ok", reveal=out)


class DeleteView(_PageToolView):
    title = "Delete pages"
    subtitle = "Remove blank, duplicate or unwanted pages. Your original stays untouched."
    action_text = "Delete & save"

    def build_options(self, f) -> None:
        self.pages = self._range_row(f, 0, "Pages to remove", "e.g. 2, 5-7")
        self.after_label = hint(f, "")
        self.after_label.grid(row=3, column=0, padx=22, pady=(14, 20), sticky="w")
        self.pages.bind("<KeyRelease>", lambda _e: self._update())

    def on_file(self) -> None:
        self._update()

    def _update(self) -> None:
        total = self.file.pages
        if not total:
            return
        try:
            gone = len(pages.pages_in(pages.parse_ranges(self.pages.get(), total)))
            self.after_label.configure(text=f"{total} pages → {total - gone} pages", text_color=t.GOLD)
        except Exception:
            self.after_label.configure(text=f"This PDF has {total} pages.", text_color=t.MUTED)

    def start(self) -> None:
        src = self.file.path
        if not src or self.worker.busy:
            return
        text = self.pages.get()
        try:
            pages.parse_ranges(text, self.file.pages)
        except Exception as exc:
            self.status.show(str(exc), "warn")
            return
        dst = ask_save_pdf(self.settings, f"{src.stem}_trimmed.pdf")
        if not dst or self.same_as_source(src, dst):
            return
        self.set_busy(True, "Removing pages…")
        self.worker.run(lambda: pages.delete_pages(src, dst, text), self._done, self._failed)

    def _done(self, out: Path) -> None:
        self.set_busy(False)
        self.status.show(f"Saved {out.name}  ·  {pages.page_count(out)} pages, "
                         f"{human_size(out.stat().st_size)}", "ok", reveal=out)
