@echo off
echo Installing dependencies...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --name AutoClicker --noconfirm auto_clicker.py

echo.
echo Done! Executable is at: dist\AutoClicker.exe
echo.
echo If you see a Windows security warning on first run, click 'More info' then 'Run anyway'.
pause
