import time
import random
import threading
import pyautogui

# Disable fail-safe to prevent accidental crashes when mouse hits screen corners
pyautogui.FAILSAFE = False


class AntiSleepWorker:
    def __init__(self, strategy, key_to_strike, pixel_distance, time_interval, use_jitter, time_min=10, time_max=30):
        self.strategy = strategy
        self.key_to_strike = key_to_strike
        self.pixel_distance = pixel_distance
        self.time_interval = time_interval
        self.use_jitter = use_jitter
        self.time_min = time_min
        self.time_max = time_max
        self.is_running = False
        self._thread = None

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._execution_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

    def _execution_loop(self):
        print(f"[INFO] Anti-Sleep engine initialized using strategy: {self.strategy}")

        key_mapping = {
            "Right Shift": "shiftright",
            "+ (Plus Key)": "+",
            "F15": "f15"
        }

        while self.is_running:
            # Determine the execution delay based on jitter settings
            if self.use_jitter:
                current_delay = random.randint(self.time_min, self.time_max)
            else:
                current_delay = self.time_interval

            print(f"[INFO] Next scheduled execution cycle in {current_delay} seconds...")

            for _ in range(current_delay):
                if not self.is_running:
                    break
                time.sleep(1)

            if not self.is_running:
                break

            try:
                if self.strategy == "Mouse Micro-Movement":
                    distance = self.pixel_distance
                    dx = random.randint(-distance, distance)
                    dy = random.randint(-distance, distance)

                    if dx == 0 and dy == 0:
                        dx = random.choice([-distance, distance]) if distance > 0 else 1

                    print(f"[ACTION] Executing smooth cursor transition: relative shift dx={dx}px, dy={dy}px")
                    pyautogui.move(dx, dy, duration=0.4)

                elif self.strategy == "Keyboard Key Strike":
                    pyautogui_key = key_mapping.get(self.key_to_strike, "shiftright")
                    print(f"[ACTION] Executing virtual keyboard event: pressing key '{pyautogui_key}'")
                    pyautogui.press(pyautogui_key)

            except Exception as error:
                print(f"[ERROR] Execution sequence failure encountered: {error}")

        print("[INFO] Anti-Sleep engine successfully stopped.")