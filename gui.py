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
        self.geometry("850x520")
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
            "time_min": 10,
            "time_max": 30
        }
        self.load_config()

        # Initialize the network update engine and pass this GUI instance to it
        self.updater = MousieUpdater(self)

        self.setup_ui()

    def setup_ui(self):
        # Main title display
        self.title_label = ctk.CTkLabel(self, text="MOUSIE AUTOMATION PLATFORM", font=("Segoe UI", 16, "bold"),
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
            self.control_frame, text="▶  START", height=45, corner_radius=8,
            fg_color="#1b5e3a", text_color="#a3e2bc", hover_color="#227a4b",
            border_width=1, border_color="#2b8c56", font=("Segoe UI", 13, "bold"),
            state="disabled", command=self.start_action
        )
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(
            self.control_frame, text="■  STOP", height=45, corner_radius=8,
            fg_color="#7a2222", text_color="#e2a3a3", hover_color="#992b2b",
            border_width=1, border_color="#bc2b2b", font=("Segoe UI", 13, "bold"),
            state="disabled", command=self.stop_action
        )
        self.btn_stop.pack(side="right", padx=5, expand=True, fill="x")

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
            scroll_container.pack(fill="both", expand=True, padx=20, pady=10)

            # 1. Strategy Selector (Mouse vs Keyboard) - Changed to CTkOptionMenu
            self.frame_strategy = ctk.CTkFrame(scroll_container, fg_color="transparent")
            self.frame_strategy.pack(fill="x", pady=(5, 12))

            lbl_strategy = ctk.CTkLabel(self.frame_strategy, text="Execution Strategy:", font=("Segoe UI", 12, "bold"),
                                        text_color="#d0dbe5")
            lbl_strategy.pack(anchor="w", pady=(0, 2))

            self.combo_strategy = ctk.CTkOptionMenu(
                self.frame_strategy, values=["Mouse Micro-Movement", "Keyboard Key Strike"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"strategy": choice}), self.save_config(),
                                        self._toggle_sleep_strategy_view(choice)]
            )
            self.combo_strategy.set(self.config_data.get("strategy", "Mouse Micro-Movement"))
            self.combo_strategy.pack(fill="x")

            # 2. Key Selection Frame - Changed to CTkOptionMenu
            self.frame_key_select = ctk.CTkFrame(scroll_container, fg_color="transparent")
            lbl_key = ctk.CTkLabel(self.frame_key_select, text="Select Key to Strike:", font=("Segoe UI", 12, "bold"),
                                   text_color="#d0dbe5")
            lbl_key.pack(anchor="w", pady=(0, 2))

            self.combo_key = ctk.CTkOptionMenu(
                self.frame_key_select, values=["Right Shift", "+ (Plus Key)", "F15"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"key_to_strike": choice}), self.save_config()]
            )
            self.combo_key.set(self.config_data.get("key_to_strike", "Right Shift"))
            self.combo_key.pack(fill="x")

            # 3. Pixel Distance Slider Frame
            self.frame_pixel_slider = ctk.CTkFrame(scroll_container, fg_color="transparent")
            self.frame_pixel_slider.pack(fill="x", pady=(0, 12))

            self.lbl_pixels = ctk.CTkLabel(self.frame_pixel_slider,
                                           text=f"Pixel Distance: {self.config_data.get('pixel_distance', 1)} px",
                                           font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            self.lbl_pixels.pack(anchor="w")

            self.slider_pixels = ctk.CTkSlider(
                self.frame_pixel_slider, from_=1, to=100, number_of_steps=99,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_pixels.configure(text=f"Pixel Distance: {int(v)} px"),
                                   self.config_data.update({"pixel_distance": int(v)}), self.save_config()]
            )
            self.slider_pixels.set(self.config_data.get("pixel_distance", 1))
            self.slider_pixels.pack(fill="x", pady=2)

            # 4. Master Time Container (Holds both slider and inputs)
            self.frame_time_master = ctk.CTkFrame(scroll_container, fg_color="transparent")
            self.frame_time_master.pack(fill="x", pady=(0, 12))

            # 4A. Single Slider View (For non-jitter mode)
            self.frame_time_slider = ctk.CTkFrame(self.frame_time_master, fg_color="transparent")
            lbl_time = ctk.CTkLabel(self.frame_time_slider, text="Exact Time Interval:", font=("Segoe UI", 12, "bold"),
                                    text_color="#d0dbe5")
            lbl_time.pack(anchor="w")

            self.lbl_time_value = ctk.CTkLabel(self.frame_time_slider,
                                               text=f"{self.config_data.get('time_interval', 10)} seconds",
                                               font=("Segoe UI", 11, "italic"), text_color="#8a99a8")
            self.lbl_time_value.pack(anchor="w", pady=(0, 2))

            self.slider_time = ctk.CTkSlider(
                self.frame_time_slider, from_=1, to=500, number_of_steps=499,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_time_value.configure(text=f"{int(v)} seconds"),
                                   self.config_data.update({"time_interval": int(v)}), self.save_config()]
            )
            self.slider_time.set(self.config_data.get("time_interval", 10))
            self.slider_time.pack(fill="x", pady=2)

            # 4B. Min/Max Input View (For jitter mode)
            self.frame_time_inputs = ctk.CTkFrame(self.frame_time_master, fg_color="transparent")
            lbl_rand_title = ctk.CTkLabel(self.frame_time_inputs, text="Randomized Execution Bounds:",
                                          font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_rand_title.pack(anchor="w", pady=(0, 5))

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

            # 5. Randomize Jitter Control Frame
            self.frame_jitter = ctk.CTkFrame(scroll_container, fg_color="transparent")
            self.frame_jitter.pack(fill="x", pady=(5, 0))

            self.switch_random = ctk.CTkSwitch(
                self.frame_jitter, text="Enable Randomized Jitter", font=("Segoe UI", 12),
                text_color="#d0dbe5", fg_color="#2a3543", progress_color="#1e90ff",
                command=self._toggle_jitter_view
            )
            if self.config_data.get("use_jitter", False):
                self.switch_random.select()
                self.frame_time_inputs.pack(fill="x")
            else:
                self.switch_random.deselect()
                self.frame_time_slider.pack(fill="x")
            self.switch_random.pack(side="left", anchor="w")

            self.btn_info = ctk.CTkButton(
                self.frame_jitter, text="ⓘ", width=20, height=20, font=("Segoe UI", 12, "bold"),
                fg_color="transparent", text_color="#1e90ff", hover_color="#2a3543",
                command=self._show_jitter_info
            )
            self.btn_info.pack(side="left", padx=8)

            # Trigger initial view layout
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

        self.btn_start.configure(state="normal")

    # --- UI HELPER METHODS FOR DYNAMIC VIEWPORTS ---
    def _toggle_sleep_strategy_view(self, choice):
        if choice == "Keyboard Key Strike":
            self.frame_pixel_slider.pack_forget()
            self.frame_key_select.pack(fill="x", pady=(0, 12), before=self.frame_time_master)
        else:
            self.frame_key_select.pack_forget()
            self.frame_pixel_slider.pack(fill="x", pady=(0, 12), before=self.frame_time_master)

    def _toggle_jitter_view(self):
        # Swaps the slider and the min/max input fields dynamically
        if self.switch_random.get():
            self.frame_time_slider.pack_forget()
            self.frame_time_inputs.pack(fill="x")
        else:
            self.frame_time_inputs.pack_forget()
            self.frame_time_slider.pack(fill="x")

        self.config_data.update({"use_jitter": self.switch_random.get()})
        self.save_config()

    def _show_jitter_info(self):
        # Clean information pop-up architecture for randomized intervals
        info_window = ctk.CTkToplevel(self)
        info_window.title("What is Randomized Jitter?")
        info_window.geometry("360x180")
        info_window.resizable(False, False)
        info_window.attributes("-topmost", True)
        info_window.configure(fg_color="#212b36")

        txt = (
            "Randomized Jitter prevents corporate monitoring algorithms from detecting "
            "automated activity.\n\n"
            "Instead of executing actions at exact static intervals (e.g., precisely every 10 seconds), "
            "it slightly shifts the delay dynamically each turn. This creates an authentic, human-like pattern."
        )

        lbl = ctk.CTkLabel(info_window, text=txt, font=("Segoe UI", 12), text_color="#d0dbe5", wraplength=320,
                           justify="left")
        lbl.pack(expand=True, padx=20, pady=(20, 10))

        btn_close = ctk.CTkButton(info_window, text="Understood", height=32, fg_color="#2a3543", text_color="#ffffff",
                                  hover_color="#364556", command=info_window.destroy)
        btn_close.pack(pady=(0, 15))

    def start_action(self):
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.tip_label.configure(text=f"STATUS: RUNNING 🚀 ({self.selected_mode.upper()} ACTIVE)", text_color="#2ed573")

        if self.selected_mode == "sleep":
            strategy = self.combo_strategy.get()
            key_to_strike = self.combo_key.get()
            pixel_distance = int(self.slider_pixels.get())
            time_interval = int(self.slider_time.get())
            use_jitter = self.switch_random.get()

            # Secure parsing for text entries to prevent crashes on non-numeric input
            try:
                time_min = int(self.entry_min.get())
                time_max = int(self.entry_max.get())
                self.config_data.update({"time_min": time_min, "time_max": time_max})
                self.save_config()
            except ValueError:
                time_min, time_max = 10, 30

            self.sleep_worker = AntiSleepWorker(
                strategy=strategy,
                key_to_strike=key_to_strike,
                pixel_distance=pixel_distance,
                time_interval=time_interval,
                use_jitter=use_jitter,
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
            except Exception as e:
                print(f"[ERROR] Failed to load local configuration file: {e}")

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, "w") as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save configuration layout state: {e}")