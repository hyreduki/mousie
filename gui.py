import customtkinter as ctk
import json
import os
from updater import MousieUpdater
from modes.sleep import AntiSleepWorker

class MousieApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.CURRENT_VERSION = "1.0.0"

        # Calculate the absolute path to guarantee correct save location permissions
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.CONFIG_FILE = os.path.join(current_directory, "config.json")

        # Window configuration
        self.title("MOUSIE v1.0.0")
        self.geometry("850x840")
        self.resizable(False, False)
        self.configure(fg_color="#1a222d")

        self.selected_mode = None
        self.is_running = False
        self.sleep_worker = None

        # Default fallback configuration dataset
        self.config_data = {
            "strategy": "Mouse Micro-Movement",
            "key_to_strike": "Right Shift",
            "pixel_distance": 1,
            "time_interval": 10,
            "use_jitter": False,
            "use_smart_idle": False,
            "idle_threshold": 300,
            "time_min": 10,
            "time_max": 30
        }
        self.load_config()

        # Initialize the network update engine and pass this GUI instance to it
        self.updater = MousieUpdater(self)

        self.setup_ui()

    def setup_ui(self):
        # Main title display
        self.title_label = ctk.CTkLabel(self, text="MOUSIE PLATFORM", font=("Segoe UI", 16, "bold"),
                                        text_color="#ffffff")
        self.title_label.pack(pady=(15, 5))

        # Main horizontal split container
        self.main_split_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split_container.pack(pady=5, padx=20, fill="both", expand=True)

        # ==========================================
        # LEFT VIEWPORT: MODE SELECTION
        # ==========================================
        self.left_frame = ctk.CTkFrame(self.main_split_container, width=280, corner_radius=10, fg_color="#212b36", border_width=1, border_color="#2d3945")
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        self.left_frame.pack_propagate(False)

        self.left_title = ctk.CTkLabel(self.left_frame, text="Select Mode", font=("Segoe UI", 13, "bold"),
                                       text_color="#8a99a8")
        self.left_title.pack(pady=(10, 5))

        button_args = {
            "master": self.left_frame,
            "height": 45,
            "corner_radius": 8,
            "fg_color": "#2a3543",
            "text_color": "#d0dbe5",
            "hover_color": "#364556",
            "border_width": 1,
            "border_color": "#3a4959",
            "font": ("Segoe UI", 13)
        }

        self.btn_sleep = ctk.CTkButton(**button_args, text="🧠  Anti-Sleep Mode",
                                       command=lambda: self.select_mode("sleep"))
        self.btn_sleep.pack(pady=6, padx=15, fill="x")

        self.btn_click = ctk.CTkButton(**button_args, text="🎮  Game Autoclicker",
                                       command=lambda: self.select_mode("click"))
        self.btn_click.pack(pady=6, padx=15, fill="x")

        self.btn_teams = ctk.CTkButton(**button_args, text="🤝  Smart Teams Mode",
                                       command=lambda: self.select_mode("teams"))
        self.btn_teams.pack(pady=6, padx=15, fill="x")

        self.btn_macro = ctk.CTkButton(**button_args, text="🎥  Macro Mode (Record/Play)",
                                       command=lambda: self.select_mode("macro"))
        self.btn_macro.pack(pady=6, padx=15, fill="x")

        # ==========================================
        # RIGHT VIEWPORT: CONFIG PANEL
        # ==========================================
        self.right_frame = ctk.CTkFrame(self.main_split_container, width=500, corner_radius=10, fg_color="#212b36", border_width=1, border_color="#2d3945")
        self.right_frame.pack(side="right", fill="both", expand=False, padx=(10, 0))
        self.right_frame.pack_propagate(False)

        self.right_title = ctk.CTkLabel(self.right_frame, text="Configuration & Status", font=("Segoe UI", 13, "bold"),
                                        text_color="#8a99a8")
        self.right_title.pack(pady=(10, 5))

        self.config_placeholder_label = ctk.CTkLabel(
            self.right_frame, text="Select a mode to configure / start", font=("Segoe UI", 13),
            text_color="#5f758a", wraplength=460, justify="center"
        )
        self.config_placeholder_label.pack(expand=True, fill="both", padx=15)

        # ==========================================
        # BOTTOM CONTROLS
        # ==========================================
        self.tip_label = ctk.CTkLabel(self, text="Please select a mode from the left panel to begin.",
                                      font=("Segoe UI", 11, "italic"), text_color="#8a99a8")
        self.tip_label.pack(pady=(5, 2))

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=(2, 15), padx=20, fill="x")

        self.btn_start = ctk.CTkButton(
            self.control_frame, text="▶  START (F8)", height=45, corner_radius=8,
            fg_color="#2a3543", text_color="#5f758a", hover_color="#2a3543",
            border_width=1, border_color="#3a4959", font=("Segoe UI", 13, "bold"),
            state="disabled", command=self.start_action
        )
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(
            self.control_frame, text="■  STOP (F8)", height=45, corner_radius=8,
            fg_color="#2a3543", text_color="#5f758a", hover_color="#2a3543",
            border_width=1, border_color="#3a4959", font=("Segoe UI", 13, "bold"),
            state="disabled", command=self.stop_action
        )
        self.btn_stop.pack(side="right", padx=5, expand=True, fill="x")

        # Bind the global F8 hotkey to the toggle logic
        self.bind_all("<F8>", self.toggle_action)

    def show_update_popup(self, new_version, github_data):
        popup = ctk.CTkToplevel(self)
        popup.title("Update Available!")
        popup.geometry("380x200")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)

        msg_label = ctk.CTkLabel(popup,
                                 text=f"A new version is available on GitHub!\n\nCurrent version: v{self.CURRENT_VERSION}\nLatest version: v{new_version}",
                                 font=("Arial", 13, "bold"))
        msg_label.pack(pady=25)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        download_url = github_data["assets"][0]["browser_download_url"]

        btn_update = ctk.CTkButton(btn_frame, text="Download Now 🚀", fg_color="#1e90ff", font=("Arial", 12, "bold"),
                                   command=lambda: [popup.destroy(), self.updater.start_download_worker(download_url)])
        btn_update.pack(side="left", expand=True, padx=5)

        btn_later = ctk.CTkButton(btn_frame, text="Later", fg_color=("#ced6e0", "#2f3542"),
                                  text_color=("#2f3542", "#f1f2f6"), command=popup.destroy)
        btn_later.pack(side="right", expand=True, padx=5)

    def select_mode(self, mode):
        if self.is_running: return
        self.selected_mode = mode
        default_bg, default_text = ("#2a3543", "#d0dbe5")
        self.btn_sleep.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_click.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_teams.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_macro.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")

        # Clear the right frame entirely to draw fresh mode-specific settings
        for widget in self.right_frame.winfo_children():
            if widget != self.right_title:
                widget.destroy()

        if mode == "sleep":
            self.btn_sleep.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.tip_label.configure(text="Anti-Sleep Mode selected. Configure your strategy and click START.")

            # Container for layout architecture inside the fixed frame
            scroll_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
            scroll_container.pack(fill="both", expand=True, padx=16, pady=14)

            # 1. Strategy section
            strategy_body = self._create_settings_section(scroll_container, "STRATEGY")

            self.frame_strategy = ctk.CTkFrame(strategy_body, fg_color="transparent")
            self.frame_strategy.pack(fill="x", pady=(0, 14))

            lbl_strategy = ctk.CTkLabel(self.frame_strategy, text="Execution Strategy:", font=("Segoe UI", 12, "bold"),
                                        text_color="#d0dbe5")
            lbl_strategy.pack(anchor="w", pady=(0, 6))

            self.combo_strategy = ctk.CTkOptionMenu(
                self.frame_strategy, values=["Mouse Micro-Movement", "Keyboard Key Strike"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"strategy": choice}), self.save_config(),
                                        self._toggle_sleep_strategy_view(choice)]
            )
            self.combo_strategy.set(self.config_data.get("strategy", "Mouse Micro-Movement"))
            self.combo_strategy.pack(fill="x")

            self.frame_strategy_details = ctk.CTkFrame(strategy_body, fg_color="transparent")
            self.frame_key_select = ctk.CTkFrame(self.frame_strategy_details, fg_color="transparent")
            lbl_key = ctk.CTkLabel(self.frame_key_select, text="Select Key to Strike:", font=("Segoe UI", 12, "bold"),
                                   text_color="#d0dbe5")
            lbl_key.pack(anchor="w", pady=(0, 6))

            self.combo_key = ctk.CTkOptionMenu(
                self.frame_key_select, values=["Right Shift", "+ (Plus Key)", "F15"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"key_to_strike": choice}), self.save_config()]
            )
            self.combo_key.set(self.config_data.get("key_to_strike", "Right Shift"))
            self.combo_key.pack(fill="x")

            self.frame_pixel_slider = ctk.CTkFrame(self.frame_strategy_details, fg_color="transparent")
            self.lbl_pixels = ctk.CTkLabel(self.frame_pixel_slider,
                                           text=f"Pixel Distance: {self.config_data.get('pixel_distance', 1)} px",
                                           font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            self.lbl_pixels.pack(anchor="w", pady=(0, 4))

            self.slider_pixels = ctk.CTkSlider(
                self.frame_pixel_slider, from_=1, to=500, number_of_steps=499,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_pixels.configure(text=f"Pixel Distance: {int(v)} px"),
                                   self.config_data.update({"pixel_distance": int(v)}), self.save_config()]
            )
            self.slider_pixels.set(self.config_data.get("pixel_distance", 1))
            self.slider_pixels.pack(fill="x", pady=(0, 4))

            # 2. Timing section
            timing_body = self._create_settings_section(scroll_container, "TIMING")

            self.frame_timing_section = timing_body
            self.frame_jitter = ctk.CTkFrame(self.frame_timing_section, fg_color="transparent")
            self.frame_jitter.pack(fill="x")

            self.switch_random = ctk.CTkSwitch(
                self.frame_jitter, text="Enable Randomized Jitter", font=("Segoe UI", 12),
                text_color="#d0dbe5", fg_color="#2a3543", progress_color="#1e90ff",
                command=self._toggle_jitter_view
            )
            self.switch_random.pack(side="left", anchor="w")

            self.btn_info = ctk.CTkButton(
                self.frame_jitter, text="ⓘ", width=20, height=20, font=("Segoe UI", 12, "bold"),
                fg_color="transparent", text_color="#1e90ff", hover_color="#2a3543"
            )
            self.btn_info.pack(side="left", padx=8)
            self.btn_info.bind(
                "<Enter>",
                lambda e: self._show_tooltip(
                    e,
                    "Randomized Jitter prevents monitoring tools from detecting automated activity.\n\n"
                    "It slightly shifts the delay dynamically each turn to create a human-like pattern."
                )
            )
            self.btn_info.bind("<Leave>", self._hide_tooltip)

            self.frame_time_master = ctk.CTkFrame(self.frame_timing_section, fg_color="transparent")

            self.frame_time_slider = ctk.CTkFrame(self.frame_time_master, fg_color="transparent")
            lbl_time = ctk.CTkLabel(self.frame_time_slider, text="Exact Time Interval:", font=("Segoe UI", 12, "bold"),
                                    text_color="#d0dbe5")
            lbl_time.pack(anchor="w", pady=(0, 4))

            self.lbl_time_value = ctk.CTkLabel(self.frame_time_slider,
                                               text=f"{self.config_data.get('time_interval', 10)} seconds",
                                               font=("Segoe UI", 11, "italic"), text_color="#8a99a8")
            self.lbl_time_value.pack(anchor="w", pady=(0, 6))

            self.slider_time = ctk.CTkSlider(
                self.frame_time_slider, from_=1, to=500, number_of_steps=499,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_time_value.configure(text=f"{int(v)} seconds"),
                                   self.config_data.update({"time_interval": int(v)}), self.save_config()]
            )
            self.slider_time.set(self.config_data.get("time_interval", 10))
            self.slider_time.pack(fill="x", pady=(0, 4))

            self.frame_time_inputs = ctk.CTkFrame(self.frame_time_master, fg_color="transparent")
            lbl_rand_title = ctk.CTkLabel(self.frame_time_inputs, text="Randomized Execution Bounds:",
                                          font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_rand_title.pack(anchor="w", pady=(0, 8))

            input_row = ctk.CTkFrame(self.frame_time_inputs, fg_color="transparent")
            input_row.pack(fill="x")

            lbl_min = ctk.CTkLabel(input_row, text="Min (sec):", font=("Segoe UI", 12), text_color="#8a99a8")
            lbl_min.pack(side="left", padx=(0, 5))
            self.entry_min = ctk.CTkEntry(input_row, width=70, fg_color="#2a3543", border_color="#3a4959",
                                          text_color="#ffffff")
            self.entry_min.insert(0, str(self.config_data.get("time_min", 10)))
            self.entry_min.pack(side="left", padx=(0, 25))

            lbl_max = ctk.CTkLabel(input_row, text="Max (sec):", font=("Segoe UI", 12), text_color="#8a99a8")
            lbl_max.pack(side="left", padx=(0, 5))
            self.entry_max = ctk.CTkEntry(input_row, width=70, fg_color="#2a3543", border_color="#3a4959",
                                          text_color="#ffffff")
            self.entry_max.insert(0, str(self.config_data.get("time_max", 30)))
            self.entry_max.pack(side="left")

            # 3. Smart idle section
            smart_idle_body = self._create_settings_section(scroll_container, "SMART IDLE")

            self.frame_smart_idle_section = smart_idle_body
            self.frame_smart_idle = ctk.CTkFrame(self.frame_smart_idle_section, fg_color="transparent")
            self.frame_smart_idle.pack(fill="x")

            self.switch_smart_idle = ctk.CTkSwitch(
                self.frame_smart_idle, text="Enable Smart Idle Detection", font=("Segoe UI", 12),
                text_color="#d0dbe5", fg_color="#2a3543", progress_color="#1e90ff",
                command=self._toggle_smart_idle_view
            )
            self.switch_smart_idle.pack(side="left", anchor="w")

            self.btn_smart_idle_info = ctk.CTkButton(
                self.frame_smart_idle, text="ⓘ", width=20, height=20, font=("Segoe UI", 12, "bold"),
                fg_color="transparent", text_color="#1e90ff", hover_color="#2a3543"
            )
            self.btn_smart_idle_info.pack(side="left", padx=8)
            self.btn_smart_idle_info.bind(
                "<Enter>",
                lambda e: self._show_tooltip(
                    e,
                    "Smart Idle Detection only acts when you are truly inactive.\n\n"
                    "It waits for the Idle Threshold before the first action, then repeats on your "
                    "set interval until you use the mouse or keyboard again."
                )
            )
            self.btn_smart_idle_info.bind("<Leave>", self._hide_tooltip)

            self.frame_idle_threshold = ctk.CTkFrame(self.frame_smart_idle_section, fg_color="transparent")
            self.frame_idle_threshold.grid_columnconfigure(0, weight=1)
            self.frame_idle_threshold.grid_rowconfigure(2, minsize=18)

            lbl_idle = ctk.CTkLabel(self.frame_idle_threshold, text="Idle Threshold (before first action):",
                                    font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_idle.grid(row=0, column=0, sticky="w", pady=(0, 4))

            self.lbl_idle_value = ctk.CTkLabel(
                self.frame_idle_threshold,
                text=f"{self.config_data.get('idle_threshold', 300)} seconds",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_idle_value.grid(row=1, column=0, sticky="w", pady=(0, 6))

            self.slider_idle_threshold = ctk.CTkSlider(
                self.frame_idle_threshold, from_=1, to=1800, number_of_steps=1799, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_idle_value.configure(text=f"{int(v)} seconds"),
                                   self.config_data.update({"idle_threshold": int(v)}), self.save_config()]
            )
            self.slider_idle_threshold.set(self.config_data.get("idle_threshold", 300))
            self.slider_idle_threshold.grid(row=2, column=0, sticky="ew", pady=(0, 4))

            # Apply initial toggle states in fixed visual order
            if self.config_data.get("use_jitter", False):
                self.switch_random.select()
            else:
                self.switch_random.deselect()
            self._toggle_jitter_view()

            if self.config_data.get("use_smart_idle", False):
                self.switch_smart_idle.select()
            else:
                self.switch_smart_idle.deselect()
            self._toggle_smart_idle_view()
            self.after(50, self._refresh_idle_slider)

            self._toggle_sleep_strategy_view(self.config_data.get("strategy", "Mouse Micro-Movement"))

        elif mode == "click":
            self.btn_click.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            lbl = ctk.CTkLabel(self.right_frame, text="🎮 Game Autoclicker Settings\n\n[Inputs pending compilation]",
                               font=("Segoe UI", 13), text_color="#5f758a")
            lbl.pack(expand=True)

        elif mode == "teams":
            self.btn_teams.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            lbl = ctk.CTkLabel(self.right_frame, text="🤝 Smart Teams Settings\n\n[Inputs pending compilation]",
                               font=("Segoe UI", 13), text_color="#5f758a")
            lbl.pack(expand=True)

        elif mode == "macro":
            self.btn_macro.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            lbl = ctk.CTkLabel(self.right_frame, text="🎥 Macro Recorder Settings\n\n[Inputs pending compilation]",
                               font=("Segoe UI", 13), text_color="#5f758a")
            lbl.pack(expand=True)

        # Light up the START button, ensure STOP is dimmed
        self.btn_start.configure(
            state="normal",
            fg_color="#1b5e3a", text_color="#a3e2bc", hover_color="#227a4b", border_color="#2b8c56"
        )
        self.btn_stop.configure(
            state="disabled",
            fg_color="#2a3543", text_color="#5f758a", hover_color="#2a3543", border_color="#3a4959"
        )

    def _create_settings_section(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="#1a222d", corner_radius=8, border_width=1, border_color="#2d3945")
        card.pack(fill="x", pady=(0, 14))

        header = ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color="#8a99a8")
        header.pack(anchor="w", padx=16, pady=(14, 10))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(0, 14))
        return body

    # --- UI HELPER METHODS FOR DYNAMIC VIEWPORTS ---
    def _toggle_sleep_strategy_view(self, choice):
        if choice == "Keyboard Key Strike":
            self.frame_pixel_slider.pack_forget()
            self.frame_key_select.pack(fill="x")
        else:
            self.frame_key_select.pack_forget()
            self.frame_pixel_slider.pack(fill="x")
        self.frame_strategy_details.pack(fill="x")

    def _toggle_jitter_view(self):
        self.frame_time_slider.pack_forget()
        self.frame_time_inputs.pack_forget()

        if self.switch_random.get():
            self.frame_time_inputs.pack(fill="x")
        else:
            self.frame_time_slider.pack(fill="x")

        self.frame_time_master.pack(fill="x", pady=(14, 0))

        self.config_data.update({"use_jitter": self.switch_random.get()})
        self.save_config()

    def _toggle_smart_idle_view(self):
        self.frame_idle_threshold.pack_forget()

        if self.switch_smart_idle.get():
            self.frame_idle_threshold.pack(fill="x", pady=(14, 0))
            self.after(10, self._refresh_idle_slider)

        self.config_data.update({"use_smart_idle": self.switch_smart_idle.get()})
        self.save_config()

    def _refresh_idle_slider(self):
        if hasattr(self, "slider_idle_threshold"):
            self.frame_idle_threshold.grid_rowconfigure(2, minsize=18)
            self.slider_idle_threshold.configure(height=16)
            self.slider_idle_threshold._draw()

    def _show_tooltip(self, event, text):
        self.tooltip = ctk.CTkToplevel(self)
        self.tooltip.overrideredirect(True)  # Removes the Windows border/title bar
        self.tooltip.attributes("-topmost", True)
        self.tooltip.configure(fg_color="#2a3543")

        # Position the tooltip slightly offset from the mouse cursor
        x = event.x_root + 15
        y = event.y_root + 15
        self.tooltip.geometry(f"+{x}+{y}")

        # Add a nice border and text
        border = ctk.CTkFrame(self.tooltip, fg_color="#212b36", border_width=1, border_color="#3a4959", corner_radius=4)
        border.pack(fill="both", expand=True)

        lbl = ctk.CTkLabel(border, text=text, font=("Segoe UI", 11), text_color="#d0dbe5", wraplength=250,
                           justify="left")
        lbl.pack(padx=12, pady=10)

    def _hide_tooltip(self, event):
        if hasattr(self, "tooltip") and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def toggle_action(self, event=None):
        if self.is_running:
            self.stop_action()
        else:
            # Only trigger start if a mode is actively selected and the start button is enabled
            if self.btn_start.cget("state") == "normal":
                self.start_action()

    def start_action(self):
        self.is_running = True

        # Dim START, Light up STOP
        self.btn_start.configure(
            state="disabled",
            fg_color="#2a3543", text_color="#5f758a", hover_color="#2a3543", border_color="#3a4959"
        )
        self.btn_stop.configure(
            state="normal",
            fg_color="#7a2222", text_color="#e2a3a3", hover_color="#992b2b", border_color="#bc2b2b"
        )

        self.tip_label.configure(text=f"STATUS: RUNNING 🚀 ({self.selected_mode.upper()} ACTIVE)", text_color="#2ed573")

        if self.selected_mode == "sleep":
            strategy = self.combo_strategy.get()
            key_to_strike = self.combo_key.get()
            pixel_distance = int(self.slider_pixels.get())
            time_interval = int(self.slider_time.get())
            use_jitter = self.switch_random.get()
            use_smart_idle = self.switch_smart_idle.get()
            idle_threshold = int(self.slider_idle_threshold.get())

            # Secure parsing for text entries to prevent crashes on non-numeric input
            try:
                time_min = int(self.entry_min.get())
                time_max = int(self.entry_max.get())
                self.config_data.update({"time_min": time_min, "time_max": time_max})
                self.save_config()
            except ValueError:
                time_min, time_max = 10, 30

            # The muted color palette for the disabled state
            disabled_text = "#5f758a"
            disabled_accent = "#3a4959"

            # Lock the UI controls and visually dim them to indicate they are frozen
            self.combo_strategy.configure(state="disabled", text_color=disabled_text, button_color=disabled_accent)
            self.combo_key.configure(state="disabled", text_color=disabled_text, button_color=disabled_accent)

            self.slider_pixels.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
            self.slider_time.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)

            self.switch_random.configure(state="disabled", text_color=disabled_text, progress_color=disabled_accent)
            self.switch_smart_idle.configure(state="disabled", text_color=disabled_text, progress_color=disabled_accent)
            self.slider_idle_threshold.configure(state="disabled", progress_color=disabled_accent,
                                                   button_color=disabled_text)

            self.entry_min.configure(state="disabled", text_color=disabled_text)
            self.entry_max.configure(state="disabled", text_color=disabled_text)

            # Dim the dynamic text labels as well for a complete locked-down look
            self.lbl_pixels.configure(text_color=disabled_text)
            self.lbl_time_value.configure(text_color=disabled_text)
            self.lbl_idle_value.configure(text_color=disabled_text)

            self.sleep_worker = AntiSleepWorker(
                strategy=strategy,
                key_to_strike=key_to_strike,
                pixel_distance=pixel_distance,
                time_interval=time_interval,
                use_jitter=use_jitter,
                use_smart_idle=use_smart_idle,
                idle_threshold=idle_threshold,
                time_min=time_min,
                time_max=time_max
            )
            self.sleep_worker.start()

    def stop_action(self):
        self.is_running = False
        self.btn_stop.configure(state="disabled")
        self.btn_start.configure(state="normal")

        if self.sleep_worker:
            self.sleep_worker.stop()
            self.sleep_worker = None

        self.select_mode(self.selected_mode)

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as file:
                    loaded_data = json.load(file)
                    # Safely merge loaded data into defaults to prevent missing key crashes
                    self.config_data.update(loaded_data)
                    self.config_data["use_jitter"] = bool(self.config_data.get("use_jitter", False))
                    self.config_data["use_smart_idle"] = bool(self.config_data.get("use_smart_idle", False))
            except Exception as e:
                print(f"[ERROR] Failed to load local configuration file: {e}")

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, "w") as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save configuration layout state: {e}")