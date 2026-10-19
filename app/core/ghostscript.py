"""Locate and run Ghostscript, the engine behind compression.

Search order:
  1. MJC_GHOSTSCRIPT environment variable (full path to the executable)
  2. A copy bundled next to the app: ghostscript/bin/gswin64c.exe
  3. Anything on PATH (gswin64c, gswin32c, gs)
  4. A normal Windows install: C:\\Program Files\\gs\\gs*\\bin\\gswin64c.exe (newest wins)
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

GS_NAMES = ("gswin64c", "gswin32c", "gs")


class GhostscriptMissing(RuntimeError):
    pass


def _app_dir() -> Path:
    # PyInstaller unpacks to sys._MEIPASS; next to the .exe is sys.executable's folder.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def _version_key(path: str) -> tuple:
    # ".../gs10.04.0/bin/..." -> (10, 4, 0)
    folder = Path(path).parents[1].name.lstrip("gs")
    return tuple(int(p) if p.isdigit() else 0 for p in folder.split("."))


def find_ghostscript() -> str | None:
    env = os.environ.get("MJC_GHOSTSCRIPT")
    if env and Path(env).is_file():
        return env

    for base in {_app_dir(), Path(sys.executable).parent}:
        for name in ("gswin64c.exe", "gswin32c.exe", "gs"):
            candidate = base / "ghostscript" / "bin" / name
            if candidate.is_file():
                return str(candidate)

    for name in GS_NAMES:
        found = shutil.which(name)
        if found:
            return found

    if sys.platform == "win32":
        installs = []
        for root in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            installs += glob.glob(os.path.join(root, "gs", "gs*", "bin", "gswin*c.exe"))
        if installs:
            return max(installs, key=_version_key)
    return None


def run_ghostscript(args: list[str]) -> None:
    exe = find_ghostscript()
    if not exe:
        raise GhostscriptMissing(
            "Ghostscript isn't installed. Get the free Windows installer from "
            "ghostscript.com/releases, install it, then restart the app."
        )
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run([exe, *args], capture_output=True, text=True, creationflags=flags)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else f"exit code {result.returncode}"
        if "password" in (result.stderr + result.stdout).lower():
            raise RuntimeError("This PDF is password-protected. Remove the password first.")
        raise RuntimeError(f"Ghostscript couldn't process this file ({tail}).")
