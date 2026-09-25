#!/bin/bash
# Builds a double-clickable Mac app from gui.py.
# Run this ON A MAC (PyInstaller cannot cross-build for other OSes).

set -e

echo "Installing PyInstaller..."
pip3 install --upgrade pyinstaller

echo "Building SmartFileOrganizer.app..."
pyinstaller --windowed --onefile \
  --name "SmartFileOrganizer" \
  --add-data "config.json:." \
  gui.py

echo ""
echo "Done. Find it at: dist/SmartFileOrganizer.app"
echo "Double-click it to run, just like any other Mac app."
echo "(First launch: right-click > Open, since it isn't Apple-notarized.)"
