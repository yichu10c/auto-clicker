#!/usr/bin/env python3
"""
Auto Clicker — ctypes version (no pynput needed on Windows)
Works on Windows (pure ctypes) and Unix (pynput fallback).
No external dependencies on Windows. Single executable when packaged.
"""
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

# ── Platform setup ────────────────────────────────────────────────────────────
PLATFORM = 'windows' if hasattr(ctypes, 'windll') else 'unix'

# ── State ─────────────────────────────────────────────────────────────────────
clicking = False
stop_event = threading.Event()
cps = 5.0
hotkey_key = 0x7A  # VK_F9
target_x, target_y = None, None
click_position_set = False

# ── Windows ctypes helpers ────────────────────────────────────────────────────
if PLATFORM == 'windows':
    user32 = ctypes.windll.user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP   = 0x0004
    PMB = ctypes.POINTER(ctypes.c_byte)

    def get_cursor_pos():
        pt = ctypes.Structure
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def win_click(x, y):
        user32.SetCursorPos(x, y)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)

# ── Unix mouse via pynput ────────────────────────────────────────────────────
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
    while not stop_event.wait(interval):
        if clicking and click_position_set:
            if PLATFORM == 'windows':
                win_click(target_x, target_y)
            else:
                unix_click(target_x, target_y)

# ── Hotkey polling (Windows) ───────────────────────────────────────────────────
def hotkey_poll():
    while not stop_event.is_set():
        if user32.GetAsyncKeyState(hotkey_key) & 0x8000:
            global clicking, click_position_set, target_x, target_y
            if not clicking:
                target_x, target_y = get_cursor_pos()
                click_position_set = True
                clicking = True
                root.after(0, lambda: status_label.config(text=f"▶ clicking @ {cps:.1f} CPS"))
            else:
                clicking = False
                root.after(0, lambda: status_label.config(text="⏹ stopped"))
            time.sleep(0.3)
        time.sleep(0.01)

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
cps_frame.pack(fill=tk.X, pady=(4, 12))
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

# Hotkey
ttk.Label(main, text="Hotkey:", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(8, 0))
hotkey_frame = ttk.Frame(main)
hotkey_frame.pack(fill=tk.X, pady=(4, 12))
hotkey_display = ttk.Label(hotkey_frame, text="F9", font=('Segoe UI', 10))
hotkey_display.pack(side=tk.LEFT)

VK_MAP = {
    'F9': 0x7A, 'F10': 0x79, 'F11': 0x7B, 'F12': 0x7C,
    'Insert': 0x2D, 'Delete': 0x2E, 'Home': 0x24, 'End': 0x23,
    'Page Up': 0x21, 'Page Down': 0x22,
    'Shift R': 0xA1, 'Ctrl R': 0xA3, 'Alt R': 0xA5,
}

def set_hotkey(name, vk):
    global hotkey_key
    hotkey_key = vk
    hotkey_display.config(text=name)

hotkey_menu = tk.Menu(root, tearoff=0)
for name, vk in VK_MAP.items():
    hotkey_menu.add_command(label=name, command=lambda n=name, v=vk: set_hotkey(n, v))

# ttk.Button menu trick — use tk.Menubutton
menubutton = tk.Menubutton(hotkey_frame, text="Change", direction='left')
menubutton['menu'] = hotkey_menu
menubutton.pack(side=tk.LEFT, padx=(8, 0))

# Status
ttk.Separator(main, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
status_label = ttk.Label(main, text="⏹ idle — hover mouse, hold HOTKEY to click",
                         font=('Segoe UI', 10), anchor='center', wraplength=220)
status_label.pack(fill=tk.X)

ttk.Label(main, text="1. Set CPS above\n2. Hover mouse over click target\n3. Hold HOTKEY to auto-click",
          font=('Segoe UI', 8), foreground='#666').pack(pady=(8, 0))

# ── Start ─────────────────────────────────────────────────────────────────────
threading.Thread(target=click_worker, daemon=True).start()
threading.Thread(target=hotkey_poll,  daemon=True).start()

root.mainloop()
