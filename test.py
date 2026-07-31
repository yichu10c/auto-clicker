import ctypes
import time
user32 = ctypes.windll.user32
VK_INSERT = 0x2D

print("Polling GetAsyncKeyState for VK_INSERT (0x2D)...")
print("Press and HOLD INSERT for 2 seconds...")
end = time.time() + 2
while time.time() < end:
    r = user32.GetAsyncKeyState(VK_INSERT)
    print(f"  GetAsyncKeyState(0x2D) = {r}  (0x8000={0x8000}, non-zero=key down)")
    time.sleep(0.1)
print("Done.")
