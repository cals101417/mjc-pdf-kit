@echo off
REM Builds "dist\MJC PDF Kit.exe". Double-click this file, or run it from a terminal.
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python isn't installed. Get Python 3.12 from python.org and tick "Add python.exe to PATH".
  pause & exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv || (pause & exit /b 1)
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller -q || (pause & exit /b 1)

if exist "ghostscript\bin\gswin64c.exe" (
  echo Bundling Ghostscript from .\ghostscript
) else (
  echo Note: no .\ghostscript folder, so the .exe will use the Ghostscript installed on each PC.
)

echo Building...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean mjc-pdf-kit.spec || (pause & exit /b 1)

echo.
echo Done: dist\MJC PDF Kit.exe
explorer dist
pause
