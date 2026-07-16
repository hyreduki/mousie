import time
import threading
import datetime
import pyautogui
import mss

pyautogui.FAILSAFE = False

BUTTON_MAP = {
    "Left Click": "left",
    "Right Click": "right",
    "Middle Click": "middle",
}

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class AutoClickWorker:
    def __init__(
        self,
        click_button,
        clicks_per_second,
        click_mode="Fixed Position",
        target_color=(255, 0, 0),
        color_tolerance=10,
        scan_region="Full Screen",
        scan_radius=200,
        scan_x=0,
        scan_y=0,
        scan_width=800,
        scan_height=600,
        scan_rate=30,
    ):
        self.click_button = click_button
        self.clicks_per_second = clicks_per_second
        self.click_mode = click_mode
        self.target_color = target_color
        self.color_tolerance = color_tolerance
        self.scan_region = scan_region
        self.scan_radius = scan_radius
        self.scan_x = scan_x
        self.scan_y = scan_y
        self.scan_width = scan_width
        self.scan_height = scan_height
        self.scan_rate = scan_rate
        self.is_running = False
        self._thread = None

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._execution_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

    def _get_ts(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _get_scan_monitor(self):
        if self.scan_region == "Around Cursor":
            x, y = pyautogui.position()
            radius = self.scan_radius
            return {
                "left": max(0, x - radius),
                "top": max(0, y - radius),
                "width": radius * 2,
                "height": radius * 2,
            }

        if self.scan_region == "Custom Region":
            return {
                "left": self.scan_x,
                "top": self.scan_y,
                "width": max(1, self.scan_width),
                "height": max(1, self.scan_height),
            }

        with mss.mss() as sct:
            return sct.monitors[1]

    def _find_color(self, monitor):
        target = self.target_color
        tolerance = self.color_tolerance

        with mss.mss() as sct:
            screenshot = sct.grab(monitor)

        if HAS_NUMPY:
            img = np.array(screenshot)
            target_bgr = np.array([target[2], target[1], target[0]])
            diff = np.abs(img[:, :, :3].astype(np.int16) - target_bgr)
            matches = np.all(diff <= tolerance, axis=2)
            coords = np.argwhere(matches)
            if len(coords) > 0:
                y, x = coords[0]
                return monitor["left"] + int(x), monitor["top"] + int(y)
            return None

        for y in range(screenshot.height):
            for x in range(screenshot.width):
                b, g, r = screenshot.pixel(x, y)[:3]
                if (
                    abs(r - target[0]) <= tolerance
                    and abs(g - target[1]) <= tolerance
                    and abs(b - target[2]) <= tolerance
                ):
                    return monitor["left"] + x, monitor["top"] + y
        return None

    def _execution_loop(self):
        button = BUTTON_MAP.get(self.click_button, "left")

        if self.click_mode == "Color Scan":
            print(
                f"[{self._get_ts()}] [INFO] Color-Scan Clicker initialized "
                f"({self.click_button}, RGB{self.target_color}, tol={self.color_tolerance})."
            )
            scan_delay = 1.0 / max(1, self.scan_rate)
            click_delay = 1.0 / max(1, self.clicks_per_second)

            while self.is_running:
                try:
                    monitor = self._get_scan_monitor()
                    match = self._find_color(monitor)
                    if match:
                        pyautogui.click(match[0], match[1], button=button)
                        time.sleep(click_delay)
                    else:
                        time.sleep(scan_delay)
                except Exception as error:
                    print(f"[{self._get_ts()}] [ERROR] Color scan failure: {error}")
                    time.sleep(scan_delay)
            return

        print(f"[{self._get_ts()}] [INFO] Auto-Clicker initialized ({self.click_button} @ {self.clicks_per_second} CPS).")
        delay = 1.0 / max(1, self.clicks_per_second)

        while self.is_running:
            try:
                pyautogui.click(button=button)
            except Exception as error:
                print(f"[{self._get_ts()}] [ERROR] Click failure: {error}")
            time.sleep(delay)
