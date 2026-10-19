"""Shared layout for every tool screen: header, body, footer (status + action)."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from .. import theme as t
from ..widgets import DropZone, StatusLine, ghost_button
from ...core.files import human_size
from ...core.pages import page_count


class ToolView(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.app = app
        self.settings = app.settings
        self.worker = app.worker
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 18))
        ctk.CTkLabel(head, text=self.title, font=t.font(24, "bold"), text_color=t.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(head, text=self.subtitle, font=t.font(13), text_color=t.MUTED,
                     anchor="w").pack(anchor="w", pady=(2, 0))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=32)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=2, column=0, sticky="ew", padx=32, pady=(14, 22))
        foot.grid_columnconfigure(0, weight=1)
        self.status = StatusLine(foot)
        self.status.grid(row=0, column=0, sticky="ew")
        self.progress = ctk.CTkProgressBar(foot, height=4, corner_radius=2, fg_color=t.SURFACE_2,
                                           progress_color=t.GOLD, mode="indeterminate")
        self.footer = foot

        self.build()

    def build(self) -> None:  # overridden by each tool
        raise NotImplementedError

    # ----- busy state -----
    def set_busy(self, busy: bool, text: str = "") -> None:
        if busy:
            self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
            self.progress.start()
            self.status.show(text or "Working…", "busy")
        else:
            self.progress.stop()
            self.progress.grid_remove()
        self.app.set_nav_enabled(not busy)

    def same_as_source(self, src: Path, dst: Path) -> bool:
        if Path(src).resolve() == Path(dst).resolve():
            self.status.show("Save under a new name. Your original file is never overwritten.", "warn")
            return True
        return False


class SingleFileField(ctk.CTkFrame):
    """Drop zone that turns into a file card once a PDF is picked."""

    def __init__(self, master, view: ToolView, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.view, self.on_change = view, on_change
        self.path: Path | None = None
        self.pages = 0
        self.grid_columnconfigure(0, weight=1)
        self.zone = DropZone(self, view.settings, self._picked, multiple=False)
        self.zone.grid(row=0, column=0, sticky="ew")

        self.card = ctk.CTkFrame(self, fg_color=t.SURFACE, corner_radius=12,
                                 border_width=1, border_color=t.BORDER)
        self.card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.card, text="PDF", width=42, height=42, corner_radius=8,
                     fg_color=t.GOLD_SOFT, text_color=t.GOLD,
                     font=t.font(12, "bold")).grid(row=0, column=0, rowspan=2, padx=16, pady=16)
        self.name = ctk.CTkLabel(self.card, text="", font=t.font(14, "bold"),
                                 text_color=t.TEXT, anchor="w")
        self.name.grid(row=0, column=1, sticky="sw", pady=(16, 0))
        self.meta = ctk.CTkLabel(self.card, text="", font=t.mono(12), text_color=t.MUTED, anchor="w")
        self.meta.grid(row=1, column=1, sticky="nw", pady=(0, 16))
        ghost_button(self.card, "Change", self.zone.browse, width=84).grid(
            row=0, column=2, rowspan=2, padx=16)

    def _picked(self, paths: list[Path]) -> None:
        path = paths[0]
        try:
            pages = page_count(path)
        except Exception as exc:
            self.view.status.show(str(exc), "error")
            return
        self.path, self.pages = path, pages
        name = path.name if len(path.name) < 60 else path.name[:57] + "…"
        self.name.configure(text=name)
        noun = "page" if pages == 1 else "pages"
        self.meta.configure(text=f"{pages} {noun}  ·  {human_size(path.stat().st_size)}")
        self.zone.grid_remove()
        self.card.grid(row=0, column=0, sticky="ew")
        self.view.status.show("")
        if self.on_change:
            self.on_change()
