#!/usr/bin/env python3
"""
Auto-clicker / Rage Clicker
- Press the hotkey to start/stop clicking at the current mouse position
- Use the GUI to set CPS (clicks per second) and choose the hotkey
"""

import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput import mouse, keyboard
from pynput.mouse import Button


# ── State ────────────────────────────────────────────────────────────────────
clicking = False
stop_event = threading.Event()
cps = 5.0
hotkey = keyboard.Key.f9
target_x, target_y = None, None
click_position_set = False

# ── Mouse click worker ────────────────────────────────────────────────────────
def click_worker():
    interval = 1.0 / cps
    while not stop_event.wait(interval):
        if clicking and click_position_set:
            mouse.Controller().position = (target_x, target_y)
            mouse.Controller().click(Button.left, 1)


# ── Keyboard listener ──────────────────────────────────────────────────────────
def on_press(key):
    global clicking, click_position_set, target_x, target_y

    if key == hotkey:
        if not clicking:
            # Set click target to current mouse position
            target_x, target_y = mouse.Controller().position
            click_position_set = True
            clicking = True
            status_label.config(text=f"�_clicking @ {cps:.1f} CPS → ({target_x}, {target_y})")
        else:
            clicking = False
            status_label.config(text="⏹ stopped")


def on_release(key):
    if key == hotkey:
        global clicking
        clicking = False
        status_label.config(text="⏹ stopped")


# ── GUI ───────────────────────────────────────────────────────────────────────
def update_hotkey_label():
    hotkey_label.config(text=f"Hotkey: {hotkey.name.upper()}")

def on_cps_changed(value):
    global cps
    cps = float(value)
    cps_label.config(text=f"{cps:.1f} CPS")

def set_hotkey(key_name):
    global hotkey
    try:
        hotkey = getattr(keyboard.Key, key_name)
        update_hotkey_label()
    except AttributeError:
        pass

def build_hotkey_menu(parent):
    menu = tk.Menu(parent, tearoff=0)
    # Common gaming keys
    for key in ['f9','f10','f11','f12','insert','delete','home','end',
                'shift_r','ctrl_r','alt_r','page_up','page_down']:
        menu.add_command(label=key.upper(), command=lambda k=key: set_hotkey(k))
    return menu

# ── Main window ───────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Auto Clicker")
root.resizable(False, False)
root.attributes('-topmost', True)

# Style
style = ttk.Style()
style.configure('TLabel', font=('Segoe UI', 10))
style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))

main = ttk.Frame(root, padding=16)
main.pack(fill=tk.BOTH)

# CPS control
ttk.Label(main, text="Clicks Per Second:", style='Header.TLabel').pack(anchor='w')
cps_frame = ttk.Frame(main)
cps_frame.pack(fill=tk.X, pady=(4, 12))
cps_slider = ttk.Scale(cps_frame, from_=1, to=50, orient='horizontal',
                        command=on_cps_changed)
cps_slider.set(cps)
cps_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
cps_label = ttk.Label(cps_frame, text=f"{cps:.1f} CPS", width=9)
cps_label.pack(side=tk.LEFT, padx=(8, 0))

# Hotkey
ttk.Label(main, text="Hotkey:", style='Header.TLabel').pack(anchor='w', pady=(8, 0))
hotkey_frame = ttk.Frame(main)
hotkey_frame.pack(fill=tk.X, pady=(4, 12))
hotkey_label = ttk.Label(hotkey_frame, text=f"{hotkey.name.upper()}", width=12)
hotkey_label.pack(side=tk.LEFT)
ttk.Button(hotkey_frame, text="Change", width=8,
           menu=build_hotkey_menu(root)).pack(side=tk.LEFT, padx=(8, 0))

# Status
ttk.Separator(main, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
status_label = ttk.Label(main, text="⏹ idle — hover mouse, hold hotkey to click",
                          style='TLabel', anchor='center', wraplength=220)
status_label.pack(fill=tk.X)

# Instructions
ttk.Label(main, text="1. Set CPS above\n2. Hover mouse over click target\n3. Hold HOTKEY to auto-click",
          font=('Segoe UI', 8), foreground='#666').pack(pady=(8, 0))


# ── Start listeners ───────────────────────────────────────────────────────────
threading.Thread(target=click_worker, daemon=True).start()
keyboard.Listener(on_press=on_press, on_release=on_release).start()

root.mainloop()
