#!/usr/bin/env python3
"""
Auto Clicker — clean rewrite
- Press any key to set hotkey
- Hold mode or Toggle mode
- pynput for keyboard + mouse (works when GUI has focus)
"""
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

PLATFORM = 'windows' if hasattr(ctypes, 'windll') else 'unix'

# ── State ─────────────────────────────────────────────────────────────────────
clicking = False
cps = 5.0
mode = 'hold'
hotkey_name = 'INSERT'
hotkey_key = 0x2D   # VK_INSERT — will be set from key capture

target_x = target_y = None
click_position_set = False

key_was_down = False

# Capture state (protected by events)
waiting_for_key = threading.Event()
captured_key = {}

# Active listener (stopped+restarted on hotkey change)
_listener = None

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
_mouse_ctrl = None
def unix_click(x, y):
    global _mouse_ctrl
    if _mouse_ctrl is None:
        _mouse_ctrl = mouse.Controller()
    _mouse_ctrl.position = (x, y)
    _mouse_ctrl.click(mouse.Button.left, 1)

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

# ── Key name helper ────────────────────────────────────────────────────────────
def get_vk(key_obj):
    """Extract virtual key code from a pynput Key or KeyCode."""
    vk = getattr(key_obj, 'vk', None)
    if vk is not None:
        return vk
    # KeyCode: try .value.vk
    val = getattr(key_obj, 'value', None)
    if val is not None:
        vk = getattr(val, 'vk', None)
        if vk is not None:
            return vk
    return None

VK_NAMES = {}
for i in range(0x30, 0x3A):   VK_NAMES[i] = chr(i)
for i in range(0x41, 0x5B):   VK_NAMES[i] = chr(i)
for i in range(0x70, 0x88):   VK_NAMES[i] = f'F{i - 0x70 + 1}'
VK_NAMES.update({
    0x08: 'BACKSPACE', 0x09: 'TAB', 0x0D: 'ENTER', 0x1B: 'ESC',
    0x20: 'SPACE',
    0x21: 'PAGE UP', 0x22: 'PAGE DOWN', 0x23: 'END',  0x24: 'HOME',
    0x25: 'LEFT', 0x26: 'UP', 0x27: 'RIGHT', 0x28: 'DOWN',
    0x2D: 'INSERT', 0x2E: 'DELETE',
})

def key_to_str(key_obj):
    vk = get_vk(key_obj)
    if vk is not None:
        return VK_NAMES.get(vk, f'KEY_{vk}')
    # special key by name
    name = getattr(key_obj, 'name', None)
    if name:
        return name.upper()
    return str(key_obj)

# ── Listener callbacks ─────────────────────────────────────────────────────────
def on_press(key):
    global clicking, key_was_down, target_x, target_y, click_position_set
    global hotkey_key, hotkey_name

    vk = get_vk(key)
    if vk is None:
        return

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
                    text=f"▶ clicking @ {cps:.1f} CPS  [{hotkey_name}] (toggle off)"))
            else:
                clicking = False
                root.after(0, lambda: status_label.config(text="⏹ stopped"))

def on_release(key):
    global clicking, key_was_down

    vk = get_vk(key)
    if vk is None or vk != hotkey_key:
        return

    key_was_down = False
    if mode == 'hold':
        clicking = False
        root.after(0, lambda: status_label.config(
            text="⏹ idle  — hold hotkey to click"))

# ── Listener lifecycle ────────────────────────────────────────────────────────
def stop_listener():
    global _listener
    if _listener is not None:
        _listener.stop()
        _listener = None

def start_listener():
    global _listener
    stop_listener()
    _listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
        suppress=False)
    _listener.start()

# ── Capture any key (blocks until key pressed) ─────────────────────────────────
def capture_key():
    """
    Runs in a thread. Waits for exactly one key press, stores it in
    captured_key dict, then exits. Safe to call multiple times.
    """
    captured_key.clear()
    evt = threading.Event()

    def _on_press(key):
        vk = get_vk(key)
        if vk is None:
            return
        captured_key['vk'] = vk
        captured_key['name'] = key_to_str(key)
        evt.set()

    def _on_release(key):
        pass

    _l = keyboard.Listener(on_press=_on_press, on_release=_on_release, suppress=False)
    _l.start()
    evt.wait()
    _l.stop()

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
    global mode, clicking, key_was_down
    mode = mode_var.get()
    key_was_down = False   # reset so next press is always clean
    if not clicking:
        desc = "hold hotkey to click, release to stop" if mode == 'hold' else "press hotkey to toggle on/off"
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
    listen_label.config(text="(press any key...)")
    threading.Thread(target=_do_capture, daemon=True).start()

def _do_capture():
    capture_key()
    vk = captured_key['vk']
    name = captured_key['name']
    global hotkey_key, hotkey_name
    hotkey_key = vk
    hotkey_name = name
    stop_listener()      # stop old listener (if any)
    time.sleep(0.1)     # small delay to ensure old listener fully stopped
    start_listener()     # start new listener with updated hotkey
    root.after(0, lambda: hotkey_display.config(text=name))
    root.after(0, lambda: listen_label.config(text=""))

ttk.Button(hotkey_frame, text="Set Hotkey", width=10, command=start_listening).pack(side=tk.LEFT, padx=(8, 0))

# Status
ttk.Separator(main, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
status_label = ttk.Label(main,
    text="⏹ idle  — hold hotkey to click",
    font=('Segoe UI', 10), anchor='center', wraplength=240)
status_label.pack(fill=tk.X)

ttk.Label(main,
    text="1. Set CPS\n2. Click Set Hotkey, then press any key\n3. Choose Hold or Toggle mode",
    font=('Segoe UI', 8), foreground='#666').pack(pady=(4, 0))

# ── Start ─────────────────────────────────────────────────────────────────────
start_listener()
threading.Thread(target=click_worker, daemon=True).start()

root.mainloop()
