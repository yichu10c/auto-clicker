#!/usr/bin/env python3
"""
Auto Clicker
- Press any key to set hotkey
- Toggle mode OR press-to-hold mode
- Works when GUI window has focus
"""
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

PLATFORM = 'windows' if hasattr(ctypes, 'windll') else 'unix'

# ── State ─────────────────────────────────────────────────────────────────────
clicking = False
cps = 5.0
mode = 'hold'
hotkey_name = 'INSERT'
hotkey_key = 0x2D   # default VK code (updated on capture)

target_x = target_y = None
click_position_set = False

# ── Windows mouse ─────────────────────────────────────────────────────────────
if PLATFORM == 'windows':
    user32 = ctypes.windll.user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP   = 0x0004

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def get_cursor_pos():
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def win_click(x, y):
        user32.SetCursorPos(x, y)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)

# ── Unix mouse ────────────────────────────────────────────────────────────────
_mouse = None
def unix_click(x, y):
    global _mouse
    if _mouse is None:
        from pynput.mouse import Button, Controller
        _mouse = Controller()
    _mouse.position = (x, y)
    _mouse.click(Button.left, 1)

# ── Click worker ───────────────────────────────────────────────────────────────
def click_worker():
    interval = 1.0 / cps
    while True:
        time.sleep(interval)
        if clicking and click_position_set:
            if PLATFORM == 'windows':
                win_click(target_x, target_y)
            else:
                unix_click(target_x, target_y)

# ── pynput keyboard listener ───────────────────────────────────────────────────
from pynput import keyboard

key_was_down = False

def on_press(key):
    global clicking, key_was_down, target_x, target_y, click_position_set, hotkey_key, hotkey_name

    try:
        vk = key.vk if hasattr(key, 'vk') else key.value.vk if hasattr(key.value, 'vk') else None
    except Exception:
        vk = None

    # Normalise to vk number
    if vk is None:
        try:
            vk = key.value.vk
        except Exception:
            return

    # Check if this is our hotkey
    if vk != hotkey_key:
        return

    if mode == 'hold':
        if not key_was_down:
            target_x, target_y = get_cursor_pos()
            click_position_set = True
            clicking = True
            key_was_down = True
            root.after(0, lambda: status_label.config(
                text=f"▶ clicking @ {cps:.1f} CPS  [{hotkey_name}]"))
    else:
        # toggle
        if not key_was_down:
            key_was_down = True
            if not clicking:
                target_x, target_y = get_cursor_pos()
                click_position_set = True
                clicking = True
                root.after(0, lambda: status_label.config(
                    text=f"▶ clicking @ {cps:.1f} CPS  [{hotkey_name}] (press again to stop)"))
            else:
                clicking = False
                root.after(0, lambda: status_label.config(text="⏹ stopped"))

def on_release(key):
    global clicking, key_was_down

    try:
        vk = key.vk if hasattr(key, 'vk') else key.value.vk if hasattr(key.value, 'vk') else None
    except Exception:
        vk = None

    if vk is None:
        try:
            vk = key.value.vk
        except Exception:
            return

    if vk != hotkey_key:
        return

    key_was_down = False

    if mode == 'hold':
        clicking = False
        root.after(0, lambda: status_label.config(
            text="⏹ idle  — release and hold hotkey to click"))

listener = None

def start_listener():
    global listener
    if listener is not None:
        listener.stop()
    listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=False)
    listener.start()

# ── Hotkey capture (any key) ──────────────────────────────────────────────────
VK_NAMES = {
    0x08: 'BACKSPACE', 0x09: 'TAB', 0x0D: 'ENTER', 0x1B: 'ESC',
    0x20: 'SPACE', 0x21: 'PAGE UP', 0x22: 'PAGE DOWN', 0x23: 'END',
    0x24: 'HOME', 0x25: 'LEFT', 0x26: 'UP', 0x27: 'RIGHT', 0x28: 'DOWN',
    0x2D: 'INSERT', 0x2E: 'DELETE',
}
for i in range(0x30, 0x3A):
    VK_NAMES[i] = chr(i)
for i in range(0x41, 0x5B):
    VK_NAMES[i] = chr(i)
for i in range(0x70, 0x88):
    VK_NAMES[i] = f'F{i - 0x70 + 1}'

def vk_to_name(vk):
    return VK_NAMES.get(vk, f'KEY_{vk}')

waiting_for_key = threading.Event()
pending_key = {}

def capture_key_thread():
    """Poll for any key press while in capture mode."""
    from pynput import keyboard as kb
    captured = {}

    def on_press(key):
        try:
            vk = key.vk if hasattr(key, 'vk') else key.value.vk if hasattr(key.value, 'vk') else None
        except Exception:
            vk = None
        if vk is None:
            try:
                vk = key.value.vk
            except Exception:
                return
        captured['vk'] = vk
        captured['name'] = vk_to_name(vk)
        waiting_for_key.set()

    def on_release(key):
        pass

    l = kb.Listener(on_press=on_press, on_release=on_release, suppress=False)
    l.start()
    waiting_for_key.wait()
    l.stop()

# ── GUI ───────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Auto Clicker")
root.resizable(False, False)
root.attributes('-topmost', True)

main = ttk.Frame(root, padding=16)
main.pack(fill=tk.BOTH)

# CPS
ttk.Label(main, text="Clicks Per Second:", font=('Segoe UI', 11, 'bold')).pack(anchor='w')
cps_frame = ttk.Frame(main)
cps_frame.pack(fill=tk.X, pady=(4, 10))
cps_slider = ttk.Scale(cps_frame, from_=1, to=50, orient='horizontal')
cps_slider.set(cps)
cps_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
cps_label = ttk.Label(cps_frame, text=f"{cps:.1f} CPS", width=9)
cps_label.pack(side=tk.LEFT, padx=(8, 0))

def on_cps_changed(*_):
    global cps
    cps = float(cps_slider.get())
    cps_label.config(text=f"{cps:.1f} CPS")

cps_slider.bind('<Motion>', on_cps_changed)
cps_slider.bind('<ButtonRelease-1>', on_cps_changed)

# Mode
ttk.Label(main, text="Click Mode:", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(4, 4))
mode_frame = ttk.Frame(main)
mode_frame.pack(fill=tk.X, pady=(0, 10))
mode_var = tk.StringVar(value='hold')

def on_mode_changed():
    global clicking, mode
    mode = mode_var.get()
    if not clicking:
        desc = "Release hotkey to stop" if mode == 'hold' else "Press hotkey to toggle"
        status_label.config(text=f"Mode: {desc}")

ttk.Radiobutton(mode_frame, text="Hold    — hold key to click, release to stop",
                variable=mode_var, value='hold', command=on_mode_changed).pack(anchor='w')
ttk.Radiobutton(mode_frame, text="Toggle  — press key to start, press again to stop",
                variable=mode_var, value='toggle', command=on_mode_changed).pack(anchor='w')

# Hotkey
ttk.Label(main, text="Hotkey:", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(4, 0))
hotkey_frame = ttk.Frame(main)
hotkey_frame.pack(fill=tk.X, pady=(4, 10))
hotkey_display = ttk.Label(hotkey_frame, text='INSERT', font=('Segoe UI', 10, 'bold'))
hotkey_display.pack(side=tk.LEFT)
listen_label = tk.Label(hotkey_frame, text="", font=('Segoe UI', 8), fg='#888')
listen_label.pack(side=tk.LEFT, padx=(8, 0))

def start_listening():
    global hotkey_key, hotkey_name
    listen_label.config(text="(press any key...)")
    waiting_for_key.clear()
    pending_key.clear()
    threading.Thread(target=capture_key_thread, daemon=True).start()
    root.after(100, check_key_press)

def check_key_press():
    if waiting_for_key.is_set():
        hotkey_key = pending_key.get('vk', 0x2D)
        hotkey_name = pending_key.get('name', 'INSERT')
        hotkey_display.config(text=hotkey_name)
        listen_label.config(text="")
        start_listener()   # restart listener with new hotkey
    else:
        root.after(100, check_key_press)

ttk.Button(hotkey_frame, text="Set Hotkey", width=10, command=start_listening).pack(side=tk.LEFT, padx=(8, 0))

# Status
ttk.Separator(main, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
status_label = ttk.Label(main,
    text="⏹ idle — hover mouse, hold hotkey to click",
    font=('Segoe UI', 10), anchor='center', wraplength=240)
status_label.pack(fill=tk.X)

ttk.Label(main, text="1. Set CPS\n2. Click Set Hotkey, then press any key\n3. Choose Hold or Toggle mode",
          font=('Segoe UI', 8), foreground='#666').pack(pady=(4, 0))

# ── Start ─────────────────────────────────────────────────────────────────────
start_listener()   # start listener with default hotkey
threading.Thread(target=click_worker, daemon=True).start()

root.mainloop()
