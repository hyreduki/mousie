import time
import random
import threading
import ctypes
import pyautogui
import datetime


# Helper voor slaap-timer monitoring
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_seconds():
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
    current_time = ctypes.windll.kernel32.GetTickCount()
    return (current_time - last_input.dwTime) / 1000


def get_last_input_tick():
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
    return last_input.dwTime


# Disable fail-safe
pyautogui.FAILSAFE = False

KEY_MAP = {
    "Right Shift": "shiftright",
    "+ (Plus Key)": "+",
    "F15": "f15",
}


class AntiSleepWorker:
    def __init__(self, strategy, key_to_strike, pixel_distance, time_interval, use_jitter, use_smart_idle=False,
                 idle_threshold=300, time_min=10, time_max=30):
        self.strategy = strategy
        self.key_to_strike = key_to_strike
        self.pixel_distance = pixel_distance
        self.time_interval = time_interval
        self.use_jitter = use_jitter
        self.use_smart_idle = use_smart_idle
        self.idle_threshold = idle_threshold
        self.time_min = time_min
        self.time_max = time_max
        self.is_running = False
        self._thread = None
        self._in_idle_session = False
        self._last_synthetic_tick = None

    def start(self):
        self.is_running = True
        self._in_idle_session = False
        self._last_synthetic_tick = None
        self._thread = threading.Thread(target=self._execution_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

    def _get_ts(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _execution_loop(self):
        print(f"[{self._get_ts()}] [INFO] Anti-Sleep engine initialized.")

        while self.is_running:
            if self.use_smart_idle:
                last_tick = get_last_input_tick()
                idle_sec = get_idle_seconds()

                if not self._in_idle_session:
                    if idle_sec < self.idle_threshold:
                        time.sleep(2)
                        continue
                    self._in_idle_session = True
                elif self._last_synthetic_tick is not None and last_tick != self._last_synthetic_tick:
                    self._in_idle_session = False
                    self._last_synthetic_tick = None
                    time.sleep(2)
                    continue

            if self.use_jitter:
                current_delay = random.randint(self.time_min, self.time_max)
            else:
                current_delay = self.time_interval

            try:
                if self.strategy == "Mouse Micro-Movement":
                    distance = self.pixel_distance
                    total_dx = random.randint(-distance, distance)
                    total_dy = random.randint(-distance, distance)
                    if total_dx == 0 and total_dy == 0: total_dx = 1

                    steps = 5
                    dx_per_step = total_dx // steps
                    dy_per_step = total_dy // steps
                    for _ in range(steps):
                        ctypes.windll.user32.mouse_event(0x0001, int(dx_per_step), int(dy_per_step), 0, 0)
                        time.sleep(0.05)
                elif self.strategy == "Keyboard Key Strike":
                    pyautogui.press(KEY_MAP.get(self.key_to_strike, "f15"))
            except Exception as error:
                print(f"[{self._get_ts()}] [ERROR] Failure: {error}")

            if self.use_smart_idle:
                self._last_synthetic_tick = get_last_input_tick()

            time.sleep(current_delay)