# PyInstaller build recipe. Run via build.bat (Windows) or: pyinstaller --noconfirm mjc-pdf-kit.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path(SPECPATH)
datas = [(str(ROOT / "assets"), "assets")]
datas += collect_data_files("customtkinter")   # theme JSON files
datas += collect_data_files("tkinterdnd2")     # tkdnd native drag-and-drop library

# Optional: bundle Ghostscript so the .exe works on PCs without it installed.
# Copy your Ghostscript install's "bin" and "lib" folders into ./ghostscript first
# (see README > "Bundle Ghostscript"). Skipped automatically if the folder is absent.
gs_dir = ROOT / "ghostscript"
if gs_dir.is_dir():
    datas.append((str(gs_dir), "ghostscript"))

a = Analysis(
    ["run.py"],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=["tkinterdnd2"],
    excludes=["pytest", "numpy"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="MJC PDF Kit",
    icon=str(ROOT / "assets" / "app.ico"),
    console=False,
    upx=False,
)
