import ctypes
import threading
from ctypes import wintypes

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_F8 = 0x77
HOTKEY_ID = 1


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class GlobalHotkeyListener:
    def __init__(self, callback):
        self.callback = callback
        self._thread = None
        self._thread_id = None
        self._running = False

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        if self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _message_loop(self):
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, 0, VK_F8):
            print("[WARN] Global F8 hotkey could not be registered (already in use?).")
            return

        msg = MSG()
        while self._running:
            result = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result <= 0:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.callback()
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
