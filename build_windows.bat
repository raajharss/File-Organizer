@echo off
REM Builds a double-clickable Windows .exe from gui.py.
REM Run this ON WINDOWS (PyInstaller cannot cross-build for other OSes).

echo Installing PyInstaller...
pip install --upgrade pyinstaller

echo Building SmartFileOrganizer.exe...
pyinstaller --windowed --onefile ^
  --name "SmartFileOrganizer" ^
  --add-data "config.json;." ^
  gui.py

echo.
echo Done. Find it at: dist\SmartFileOrganizer.exe
echo Double-click it to run, just like any other Windows program.
pause
