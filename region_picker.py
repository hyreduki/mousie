import tkinter as tk


class RegionPickerOverlay:
    MIN_SIZE = 10

    def __init__(self, master, on_complete, on_cancel=None):
        self.master = master
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.overlay = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None

    def open(self):
        self.overlay = tk.Toplevel(self.master)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.35)
        self.overlay.configure(bg="#000000", cursor="crosshair")

        screen_w = self.overlay.winfo_screenwidth()
        screen_h = self.overlay.winfo_screenheight()
        self.overlay.geometry(f"{screen_w}x{screen_h}+0+0")

        self.canvas = tk.Canvas(
            self.overlay,
            cursor="crosshair",
            highlightthickness=0,
            bg="#000000",
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.instruction = tk.Label(
            self.overlay,
            text="Drag to select scan region  •  Esc to cancel",
            font=("Segoe UI", 13, "bold"),
            bg="#1a222d",
            fg="#ffffff",
            padx=16,
            pady=10,
        )
        self.instruction.place(relx=0.5, y=24, anchor="n")

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.overlay.bind("<Escape>", self._cancel)
        self.canvas.bind("<Escape>", self._cancel)
        self.overlay.focus_force()

    def _root_to_canvas(self, x_root, y_root):
        return x_root - self.overlay.winfo_rootx(), y_root - self.overlay.winfo_rooty()

    def _on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        cx, cy = self._root_to_canvas(event.x_root, event.y_root)
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            cx, cy, cx, cy,
            outline="#1e90ff",
            width=3,
        )

    def _on_drag(self, event):
        if self.rect_id is None or self.start_x is None:
            return
        sx, sy = self._root_to_canvas(self.start_x, self.start_y)
        ex, ey = self._root_to_canvas(event.x_root, event.y_root)
        self.canvas.coords(self.rect_id, sx, sy, ex, ey)

    def _on_release(self, event):
        if self.start_x is None:
            self._cancel()
            return

        left = min(self.start_x, event.x_root)
        top = min(self.start_y, event.y_root)
        width = abs(event.x_root - self.start_x)
        height = abs(event.y_root - self.start_y)

        self._close()

        if width >= self.MIN_SIZE and height >= self.MIN_SIZE:
            self.on_complete(int(left), int(top), int(width), int(height))
        elif self.on_cancel:
            self.on_cancel()

    def _cancel(self, _event=None):
        self._close()
        if self.on_cancel:
            self.on_cancel()

    def _close(self):
        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.overlay = None
        self.canvas = None
        self.rect_id = None
        self.start_x = None
        self.start_y = None
