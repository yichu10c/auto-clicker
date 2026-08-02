# Auto Clicker

A lightweight Windows auto-clicker with a clean GUI — no dependencies required to run the `.exe`.

## Features

- **Any key as hotkey** — click Set Hotkey, then press any key to bind it
- **Hold mode** — hold the hotkey to click continuously; release to stop
- **Toggle mode** — press once to start clicking, press again to stop
- **Adjustable CPS** — 1 to 50 clicks per second via slider
- **Single .exe** — no Python installation needed to run

## Requirements to build from source

- Python 3.8+
- `pip install pyinstaller pynput`

## Build

```bash
# Windows
build.bat

# macOS / Linux
chmod +x build.sh && ./build.sh
```

The executable will be at `dist/AutoClicker.exe`.

## Run without building

```bash
python auto_clicker.py
```

Requires: `pip install pynput`
