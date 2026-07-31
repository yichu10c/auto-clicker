#!/usr/bin/env python3
"""
Auto Clicker — ctypes version (no pynput needed on Windows)
Works on Windows (pure ctypes) and Unix (pynput fallback).
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
cps = 5.0
hotkey_key = 0x2D       # VK_INSERT — not intercepted by console
target_x = target_y = None
click_position_set = False

# ── Windows ctypes helpers ────────────────────────────────────────────────────
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
    while True:
        time.sleep(interval)
        if clicking and click_position_set:
            if PLATFORM == 'windows':
                win_click(target_x, target_y)
            else:
                unix_click(target_x, target_y)

# ── Hotkey polling (Windows) ───────────────────────────────────────────────────
def hotkey_poll():
    while True:
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
            time.sleep(0.25)
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

hotkey_display = ttk.Label(hotkey_frame, text="INSERT", font=('Segoe UI', 10))
hotkey_display.pack(side=tk.LEFT)

VK_MAP = {
    'INSERT':    0x2D,
    'DELETE':    0x2E,
    'HOME':      0x24,
    'END':       0x23,
    'PAGE UP':   0x21,
    'PAGE DOWN': 0x22,
    'F9':        0x7A,
    'F10':       0x79,
    'F11':       0x7B,
    'F12':       0x7C,
}

def set_hotkey(name, vk):
    global hotkey_key
    hotkey_key = vk
    hotkey_display.config(text=name)

# Use a simple dropdown (OptionMenu) instead of a broken menu button
def show_hotkey_menu():
    menu = tk.Toplevel(root)
    menu.title("Choose Hotkey")
    menu.resizable(False, False)
    menu.attributes('-topmost', True)
    x = root.winfo_rootx() + hotkey_frame.winfo_x()
    y = root.winfo_rooty() + hotkey_frame.winfo_y() + hotkey_frame.winfo_height()
    menu.geometry(f"+{x}+{y}")

    for name, vk in VK_MAP.items():
        tk.Button(menu, text=name, font=('Segoe UI', 10),
                   command=lambda n=name, v=vk: [set_hotkey(n, v), menu.destroy()],
                   width=12).pack(padx=4, pady=2)

    tk.Button(menu, text="Cancel", font=('Segoe UI', 9),
               command=menu.destroy).pack(pady=(4, 0))

ttk.Button(hotkey_frame, text="Change", width=8, command=show_hotkey_menu).pack(side=tk.LEFT, padx=(8, 0))

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
