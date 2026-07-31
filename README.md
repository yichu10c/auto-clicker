# Auto Clicker

A simple rage clicker / auto clicker with a lightweight GUI.

![Auto Clicker](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)

## Features

- **Adjustable CPS** — 1 to 50 clicks per second via slider
- **Customizable hotkey** — bind to any key (default: F9)
- **Click at mouse position** — hover anywhere, hotkey starts clicking there
- **Single executable** — no Python or dependencies needed on the target machine

## Download

Pre-built executables coming soon. For now, build it yourself (see below).

## Build from Source

### Requirements
- Python 3.8+
- `pip`

### Build

```bash
git clone https://github.com/yichu10c/auto-clicker.git
cd auto-clicker
chmod +x build.sh
./build.sh
```

The executable will be at `dist/AutoClicker`.

### macOS first-run
If blocked by system security on first run:
```bash
xattr -d com.apple.quarantine dist/AutoClicker
```

### Linux first-run
```bash
chmod +x dist/AutoClicker
```

## Usage

1. Set your desired **CPS** (clicks per second) with the slider
2. Hover your mouse over the target click location
3. **Hold the hotkey** to auto-click — release to stop
4. Change the hotkey via the **Change** button if F9 is taken

## Controls

| Setting | Default | Description |
|---------|---------|-------------|
| CPS | 5 | Clicks per second (1–50) |
| Hotkey | F9 | Key that starts/stops clicking |
