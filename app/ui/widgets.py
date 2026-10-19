"""Reusable branded widgets: buttons, cards, drop zone, file picker, status line."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from . import theme as t

try:
    from tkinterdnd2 import DND_FILES
except ImportError:  # drag-and-drop is optional; Browse always works
    DND_FILES = None

DND_READY = False  # flipped on by the window once tkdnd loads


def open_in_explorer(path: Path) -> None:
    path = Path(path)
    try:
        if sys.platform == "win32":
            if path.is_file():
                subprocess.run(["explorer", "/select,", str(path)])
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R" if path.is_file() else "", str(path)])
        else:
            subprocess.run(["xdg-open", str(path.parent if path.is_file() else path)])
    except OSError:
        pass


# ---------- buttons & text ----------
class PrimaryButton(ctk.CTkButton):
    """Gold call-to-action. Looks clearly inactive when disabled."""

    def __init__(self, master, text: str, command: Callable, width: int = 0, **kw):
        super().__init__(master, text=text, command=command, height=42, corner_radius=t.RADIUS,
                         fg_color=t.GOLD, hover_color=t.GOLD_HOVER, text_color=t.ON_GOLD,
                         text_color_disabled=t.FAINT, font=t.font(14, "bold"),
                         width=width or 140, **kw)

    def set_enabled(self, on: bool, text: str | None = None) -> None:
        kw = {"text": text} if text else {}
        self.configure(state="normal" if on else "disabled",
                       fg_color=t.GOLD if on else t.SURFACE_2, **kw)


def primary_button(master, text: str, command: Callable, width: int = 0, **kw) -> PrimaryButton:
    return PrimaryButton(master, text, command, width, **kw)


def ghost_button(master, text: str, command: Callable, width: int = 0, **kw) -> ctk.CTkButton:
    return ctk.CTkButton(
        master, text=text, command=command, height=34, corner_radius=8,
        fg_color="transparent", hover_color=t.SURFACE_2, border_width=1,
        border_color=t.BORDER_STRONG, text_color=t.TEXT, font=t.font(13), width=width or 90, **kw)


def icon_button(master, text: str, command: Callable, tooltip_color: str = t.MUTED) -> ctk.CTkButton:
    return ctk.CTkButton(
        master, text=text, command=command, width=28, height=28, corner_radius=6,
        fg_color="transparent", hover_color=t.SURFACE_2, text_color=tooltip_color, font=t.font(14))


def section_label(master, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(master, text=text.upper(), font=t.font(11, "bold"),
                        text_color=t.FAINT, anchor="w")


def card(master, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, fg_color=t.SURFACE, corner_radius=12,
                        border_width=1, border_color=t.BORDER, **kw)


def segmented(master, values: list[str], command: Callable | None = None, **kw) -> ctk.CTkSegmentedButton:
    return ctk.CTkSegmentedButton(
        master, values=values, command=command, height=34, corner_radius=8,
        fg_color=t.SURFACE_2, selected_color=t.GOLD, selected_hover_color=t.GOLD_HOVER,
        unselected_color=t.SURFACE_2, unselected_hover_color=t.BORDER_STRONG,
        text_color=t.TEXT, font=t.font(12, "bold"), **kw)


def switch(master, text: str, variable, command: Callable | None = None) -> ctk.CTkSwitch:
    return ctk.CTkSwitch(
        master, text=text, variable=variable, command=command, font=t.font(13),
        text_color=t.TEXT, progress_color=t.GOLD, button_color=t.TEXT,
        button_hover_color="#FFFFFF", fg_color=t.BORDER_STRONG)


def entry(master, placeholder: str = "", width: int = 200, **kw) -> ctk.CTkEntry:
    return ctk.CTkEntry(
        master, placeholder_text=placeholder, width=width, height=36, corner_radius=8,
        fg_color=t.SURFACE_2, border_color=t.BORDER_STRONG, border_width=1,
        text_color=t.TEXT, placeholder_text_color=t.FAINT, font=t.font(13), **kw)


def hint(master, text: str, **kw) -> ctk.CTkLabel:
    return ctk.CTkLabel(master, text=text, font=t.font(12), text_color=t.MUTED,
                        anchor="w", justify="left", **kw)


# ---------- dialogs ----------
PDF_TYPES = [("PDF files", "*.pdf"), ("All files", "*.*")]


def ask_pdfs(settings, multiple: bool = True) -> list[Path]:
    initial = settings.get("last_dir") or str(Path.home())
    if multiple:
        picked = filedialog.askopenfilenames(filetypes=PDF_TYPES, initialdir=initial)
    else:
        one = filedialog.askopenfilename(filetypes=PDF_TYPES, initialdir=initial)
        picked = (one,) if one else ()
    paths = [Path(p) for p in picked]
    if paths:
        settings["last_dir"] = str(paths[0].parent)
    return paths


def ask_save_pdf(settings, suggested: str) -> Path | None:
    out = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=PDF_TYPES, initialfile=suggested,
        initialdir=settings.get("last_dir") or str(Path.home()))
    return Path(out) if out else None


def ask_folder(settings) -> Path | None:
    out = filedialog.askdirectory(initialdir=settings.get("last_dir") or str(Path.home()))
    return Path(out) if out else None


# ---------- drop zone ----------
class DropZone(ctk.CTkFrame):
    """Click to browse, or drop PDFs from Explorer."""

    def __init__(self, master, settings, on_files: Callable[[list[Path]], None],
                 multiple: bool = True, height: int = 132):
        super().__init__(master, height=height, fg_color=t.SURFACE, corner_radius=14,
                         border_width=2, border_color=t.BORDER_STRONG)
        self.settings, self.on_files, self.multiple = settings, on_files, multiple
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 4), weight=1)

        badge = ctk.CTkLabel(self, text="PDF", width=46, height=30, corner_radius=7,
                             fg_color=t.GOLD_SOFT, text_color=t.GOLD, font=t.font(12, "bold"))
        badge.grid(row=1, column=0, pady=(0, 8))
        noun = "PDFs" if multiple else "a PDF"
        drop = "Drop " + noun + " here" if DND_READY else "Choose " + noun
        self.title = ctk.CTkLabel(self, text=drop, font=t.font(15, "bold"), text_color=t.TEXT)
        self.title.grid(row=2, column=0)
        sub = "or click to browse your files" if DND_READY else "click anywhere in this box"
        self.sub = ctk.CTkLabel(self, text=sub, font=t.font(12), text_color=t.MUTED)
        self.sub.grid(row=3, column=0)

        for widget in self._all_widgets():
            widget.bind("<Button-1>", lambda _e: self.browse(), add="+")
            widget.bind("<Enter>", lambda _e: self._hover(True), add="+")
            widget.bind("<Leave>", lambda _e: self._hover(False), add="+")
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass
            if DND_READY and DND_FILES:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._dropped)
                widget.dnd_bind("<<DropEnter>>", lambda e: (self._hover(True), e.action)[1])
                widget.dnd_bind("<<DropLeave>>", lambda e: (self._hover(False), e.action)[1])

    def _all_widgets(self):
        stack, seen = [self], []
        while stack:
            w = stack.pop()
            seen.append(w)
            stack.extend(w.winfo_children())
        return seen

    def _hover(self, on: bool) -> None:
        self.configure(border_color=t.GOLD if on else t.BORDER_STRONG,
                       fg_color=t.SURFACE_2 if on else t.SURFACE)

    def browse(self) -> None:
        paths = ask_pdfs(self.settings, self.multiple)
        if paths:
            self.on_files(paths)

    def _dropped(self, event):
        self._hover(False)
        raw = self.tk.splitlist(event.data)
        paths = []
        for item in raw:
            p = Path(item)
            if p.is_dir():
                paths += sorted(p.glob("*.pdf")) + sorted(p.glob("*.PDF"))
            elif p.suffix.lower() == ".pdf":
                paths.append(p)
        if not self.multiple:
            paths = paths[:1]
        if paths:
            self.settings["last_dir"] = str(paths[0].parent)
            self.on_files(paths)
        return event.action


# ---------- status line ----------
class StatusLine(ctk.CTkFrame):
    COLORS = {"info": t.MUTED, "ok": t.SUCCESS, "warn": t.WARNING, "error": t.DANGER, "busy": t.BLUE}

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(1, weight=1)
        self.dot = ctk.CTkLabel(self, text="", font=t.font(11), text_color=t.FAINT, width=14)
        self.dot.grid(row=0, column=0, padx=(0, 6))
        self.label = ctk.CTkLabel(self, text="", font=t.font(12), text_color=t.MUTED,
                                  anchor="w", justify="left", wraplength=520)
        self.label.grid(row=0, column=1, sticky="ew")
        self.action = None

    def show(self, text: str, kind: str = "info", reveal: Path | None = None) -> None:
        color = self.COLORS.get(kind, t.MUTED)
        self.dot.configure(text_color=color, text="●" if text else "")
        self.label.configure(text=text, text_color=t.TEXT if kind in ("ok", "error") else t.MUTED)
        if self.action:
            self.action.destroy()
            self.action = None
        if reveal:
            self.action = ghost_button(self, "Show in folder", lambda: open_in_explorer(reveal), width=120)
            self.action.grid(row=0, column=2, padx=(10, 0))
