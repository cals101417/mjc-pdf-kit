"""Main window: branded sidebar + one tool view at a time."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import customtkinter as ctk

from . import theme as t
from . import widgets
from .views.compress import CompressView
from .views.merge import MergeView
from .views.pagetools import DeleteView, RotateView, SplitView
from .worker import Worker
from ..config import APP_NAME, AUTHOR, SITE_LABEL, SITE_URL, VERSION
from ..core.ghostscript import find_ghostscript
from ..settings import Settings

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

NAV = [
    ("compress", "Compress", CompressView),
    ("merge", "Merge", MergeView),
    ("split", "Split & extract", SplitView),
    ("rotate", "Rotate", RotateView),
    ("delete", "Delete pages", DeleteView),
]


def asset(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / "assets" / name


class App(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=t.BG)
        t.apply()
        if TkinterDnD is not None:
            try:
                TkinterDnD._require(self)
                widgets.DND_READY = True
            except Exception:
                widgets.DND_READY = False

        self.title(APP_NAME)
        self.geometry("1120x740")
        self.minsize(980, 660)
        icon = asset("app.ico")
        if sys.platform == "win32" and icon.exists():
            self.iconbitmap(str(icon))

        self.settings = Settings()
        self.worker = Worker(self)
        self.ghostscript = find_ghostscript()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.stage = ctk.CTkFrame(self, fg_color=t.BG, corner_radius=0)
        self.stage.grid(row=0, column=1, sticky="nsew")
        self.stage.grid_columnconfigure(0, weight=1)
        self.stage.grid_rowconfigure(0, weight=1)

        self.views: dict[str, ctk.CTkFrame] = {}
        self.current = None
        self.show("compress")
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ----- sidebar -----
    def _build_sidebar(self) -> None:
        side = ctk.CTkFrame(self, width=232, fg_color=t.SIDEBAR, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(side, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(26, 30))
        self._logo(brand).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(brand, text="PDF Kit", font=t.font(17, "bold"), text_color=t.TEXT,
                     anchor="w").grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(brand, text=f"by {AUTHOR}", font=t.font(11), text_color=t.MUTED,
                     anchor="w").grid(row=1, column=1, sticky="nw")

        ctk.CTkLabel(side, text="TOOLS", font=t.font(11, "bold"), text_color=t.FAINT,
                     anchor="w").grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 6))
        self.nav_buttons: dict[str, tuple[ctk.CTkFrame, ctk.CTkButton]] = {}
        for i, (key, label, _view) in enumerate(NAV):
            holder = ctk.CTkFrame(side, fg_color="transparent")
            holder.grid(row=2 + i, column=0, sticky="ew", padx=(0, 14), pady=2)
            holder.grid_columnconfigure(1, weight=1)
            bar = ctk.CTkFrame(holder, width=3, height=26, corner_radius=2, fg_color="transparent")
            bar.grid(row=0, column=0, padx=(0, 11))
            btn = ctk.CTkButton(holder, text=label, anchor="w", height=38, corner_radius=8,
                                fg_color="transparent", hover_color=t.SURFACE, text_color=t.MUTED,
                                font=t.font(14), command=lambda k=key: self.show(k))
            btn.grid(row=0, column=1, sticky="ew")
            self.nav_buttons[key] = (bar, btn)

        side.grid_rowconfigure(20, weight=1)
        foot = ctk.CTkFrame(side, fg_color="transparent")
        foot.grid(row=21, column=0, sticky="ew", padx=24, pady=(0, 22))

        ok = bool(self.ghostscript)
        engine = ctk.CTkFrame(foot, fg_color=t.SURFACE, corner_radius=8)
        engine.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(engine, text="●", font=t.font(10), width=12,
                     text_color=t.SUCCESS if ok else t.WARNING).pack(side="left", padx=(10, 6), pady=8)
        ctk.CTkLabel(engine, text="Engine ready" if ok else "Ghostscript missing",
                     font=t.font(12), text_color=t.TEXT if ok else t.WARNING).pack(side="left")
        if not ok:
            ctk.CTkButton(engine, text="Get it", width=44, height=22, fg_color="transparent",
                          hover_color=t.SURFACE_2, text_color=t.BLUE, font=t.font(12),
                          command=lambda: webbrowser.open("https://ghostscript.com/releases/gsdnld.html")
                          ).pack(side="right", padx=6)

        ctk.CTkLabel(foot, text="100% offline. Files never leave your PC.", font=t.font(11),
                     text_color=t.FAINT, anchor="w", justify="left", wraplength=180).pack(fill="x")
        link = ctk.CTkLabel(foot, text=SITE_LABEL, font=t.font(12), text_color=t.BLUE,
                            anchor="w", cursor="hand2")
        link.pack(fill="x", pady=(8, 0))
        link.bind("<Button-1>", lambda _e: webbrowser.open(SITE_URL))
        ctk.CTkLabel(foot, text=f"v{VERSION}", font=t.mono(10), text_color=t.FAINT,
                     anchor="w").pack(fill="x")

    def _logo(self, master) -> ctk.CTkLabel:
        """Uses assets/logo.png (your MJC mark) when present; otherwise a gold monogram."""
        path = asset("logo.png")
        if path.exists():
            from PIL import Image
            img = ctk.CTkImage(Image.open(path), size=(40, 40))
            return ctk.CTkLabel(master, image=img, text="")
        return ctk.CTkLabel(master, text="MJC", width=42, height=42, corner_radius=10,
                            fg_color=t.GOLD, text_color=t.ON_GOLD, font=t.font(13, "bold"))

    # ----- navigation -----
    def show(self, key: str) -> None:
        if self.worker.busy:
            return
        if key not in self.views:
            view_cls = next(v for k, _l, v in NAV if k == key)
            self.views[key] = view_cls(self.stage, self)
        if self.current:
            self.current.grid_remove()
        self.current = self.views[key]
        self.current.grid(row=0, column=0, sticky="nsew")
        for k, (bar, btn) in self.nav_buttons.items():
            active = k == key
            bar.configure(fg_color=t.GOLD if active else "transparent")
            btn.configure(fg_color=t.SURFACE if active else "transparent",
                          text_color=t.TEXT if active else t.MUTED,
                          font=t.font(14, "bold" if active else "normal"))

    def set_nav_enabled(self, enabled: bool) -> None:
        for _bar, btn in self.nav_buttons.values():
            btn.configure(state="normal" if enabled else "disabled")

    def _close(self) -> None:
        self.settings.save()
        self.destroy()
