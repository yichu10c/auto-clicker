@echo off
:: Build Auto Clicker as a single .exe using PyInstaller
:: Requirements: Python 3.8+ with tkinter, ctypes (stdlib), pynput

echo Installing dependencies...
pip install pyinstaller pynput

echo Building...
pyinstaller --onefile --windowed --name AutoClicker auto_clicker.py

echo.
echo Done! Executable is in dist\AutoClicker.exe
pause
