import customtkinter as ctk
import json
import os
import sys
from updater import MousieUpdater
from hotkey import GlobalHotkeyListener
from modes.sleep import AntiSleepWorker
from modes.click import AutoClickWorker
from modes.ghost import ProcessGhost, GHOST_PROCESS_OPTIONS, is_frozen
from region_picker import RegionPickerOverlay

class MousieApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.CURRENT_VERSION = "1.0.0"

        # Calculate the absolute path to guarantee correct save location permissions
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.CONFIG_FILE = os.path.join(current_directory, "config.json")

        # Window configuration
        self.title("MOUSIE v1.0.0")
        self.geometry("850x720")
        self.resizable(False, False)
        self.configure(fg_color="#1a222d")

        self.selected_mode = None
        self.is_running = False
        self.sleep_worker = None
        self.click_worker = None
        self.process_ghost = None
        self._region_picker = None

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
            "time_max": 30,
            "click_button": "Left Click",
            "clicks_per_second": 10,
            "click_mode": "Fixed Position",
            "target_color_r": 255,
            "target_color_g": 0,
            "target_color_b": 0,
            "color_tolerance": 10,
            "scan_region": "Full Screen",
            "scan_radius": 200,
            "scan_x": 0,
            "scan_y": 0,
            "scan_width": 800,
            "scan_height": 600,
            "scan_rate": 30,
            "use_process_ghost": False,
            "ghost_process_name": "RuntimeBroker.exe",
        }
        self.load_config()

        # Initialize the network update engine and pass this GUI instance to it
        self.updater = MousieUpdater(self)

        self.setup_ui()
        self.hotkey_listener = GlobalHotkeyListener(lambda: self.after(0, self.toggle_action))
        self.hotkey_listener.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self._region_picker is not None:
            self._region_picker._close()
            self._region_picker = None
        if self.is_running:
            self.stop_action()
        self.hotkey_listener.stop()
        self.destroy()

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

        self.btn_sleep = ctk.CTkButton(**button_args, text="Anti-Sleep Mode",
                                       command=lambda: self.select_mode("sleep"))
        self.btn_sleep.pack(pady=6, padx=15, fill="x")

        self.btn_click = ctk.CTkButton(**button_args, text="Autoclicker",
                                       command=lambda: self.select_mode("click"))
        self.btn_click.pack(pady=6, padx=15, fill="x")

        self.btn_teams = ctk.CTkButton(**button_args, text="Smart Teams Mode",
                                       command=lambda: self.select_mode("teams"))
        self.btn_teams.pack(pady=6, padx=15, fill="x")

        self.btn_macro = ctk.CTkButton(**button_args, text="Macro Mode (Record/Play)",
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
            scroll_container = self._create_config_scroll_container(self.right_frame)
            self._create_mode_banner(
                scroll_container,
                "Anti-Sleep Mode",
                "Keeps your system active. Configure how, when, and optionally disguise the process."
            )

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
            self.frame_strategy_details.pack(fill="x", pady=(14, 0))

            self.frame_key_select = ctk.CTkFrame(self.frame_strategy_details, fg_color="transparent")
            self.lbl_key = ctk.CTkLabel(self.frame_key_select, text="Select Key to Strike:", font=("Segoe UI", 12, "bold"),
                                   text_color="#d0dbe5")
            self.lbl_key.pack(anchor="w", pady=(0, 6))

            self.combo_key = ctk.CTkOptionMenu(
                self.frame_key_select, values=["Right Shift", "+ (Plus Key)", "F15"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"key_to_strike": choice}), self.save_config()]
            )
            self.combo_key.set(self.config_data.get("key_to_strike", "Right Shift"))
            self.combo_key.pack(fill="x")
            self.frame_key_select.pack(fill="x")

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
            self.frame_pixel_slider.pack(fill="x", pady=(14, 0))

            # 2. Timing section
            timing_body = self._create_settings_section(scroll_container, "TIMING")

            self.frame_timing_section = timing_body

            self.frame_time_slider = ctk.CTkFrame(self.frame_timing_section, fg_color="transparent")
            self.frame_time_slider.pack(fill="x")

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

            self._create_subsection_label(self.frame_timing_section, "OPTIONAL")

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

            self.frame_time_inputs = ctk.CTkFrame(self.frame_timing_section, fg_color="transparent")
            self.frame_time_inputs.pack(fill="x", pady=(10, 0))

            lbl_rand_title = ctk.CTkLabel(self.frame_time_inputs, text="Randomized Execution Bounds:",
                                          font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_rand_title.pack(anchor="w", pady=(0, 8))
            self.lbl_rand_title = lbl_rand_title

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

            self.frame_time_master = self.frame_time_slider  # legacy ref for start_action if needed

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
            self.lbl_idle = lbl_idle

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
            self.frame_idle_threshold.pack(fill="x", pady=(14, 0))

            # 4. Process ghosting section
            ghost_body = self._create_settings_section(scroll_container, "PROCESS GHOSTING")

            self.frame_ghost_section = ghost_body
            self.frame_ghost_switch = ctk.CTkFrame(self.frame_ghost_section, fg_color="transparent")
            self.frame_ghost_switch.pack(fill="x")

            self.switch_process_ghost = ctk.CTkSwitch(
                self.frame_ghost_switch, text="Enable Process Ghosting", font=("Segoe UI", 12),
                text_color="#d0dbe5", fg_color="#2a3543", progress_color="#1e90ff",
                command=self._toggle_ghost_view
            )
            self.switch_process_ghost.pack(side="left", anchor="w")

            self.btn_ghost_info = ctk.CTkButton(
                self.frame_ghost_switch, text="ⓘ", width=20, height=20, font=("Segoe UI", 12, "bold"),
                fg_color="transparent", text_color="#1e90ff", hover_color="#2a3543"
            )
            self.btn_ghost_info.pack(side="left", padx=8)
            self.btn_ghost_info.bind(
                "<Enter>",
                lambda e: self._show_tooltip(
                    e,
                    "Disguises Mousie as a harmless system process.\n\n"
                    "The window title and taskbar entry are hidden while active. "
                    "When running as a built .exe, the worker also launches under "
                    "the selected process name in Task Manager."
                )
            )
            self.btn_ghost_info.bind("<Leave>", self._hide_tooltip)

            self.frame_ghost_select = ctk.CTkFrame(self.frame_ghost_section, fg_color="transparent")
            self.lbl_ghost = ctk.CTkLabel(self.frame_ghost_select, text="Disguise As:", font=("Segoe UI", 12, "bold"),
                                     text_color="#d0dbe5")
            self.lbl_ghost.pack(anchor="w", pady=(0, 6))

            self.combo_ghost_process = ctk.CTkOptionMenu(
                self.frame_ghost_select, values=GHOST_PROCESS_OPTIONS,
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"ghost_process_name": choice}), self.save_config()]
            )
            self.combo_ghost_process.set(self.config_data.get("ghost_process_name", "RuntimeBroker.exe"))
            self.combo_ghost_process.pack(fill="x")
            self.frame_ghost_select.pack(fill="x", pady=(14, 0))

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

            if self.config_data.get("use_process_ghost", False):
                self.switch_process_ghost.select()
            else:
                self.switch_process_ghost.deselect()
            self._toggle_ghost_view()

            self._toggle_sleep_strategy_view(self.config_data.get("strategy", "Mouse Micro-Movement"))
            self._apply_slider_scroll_passthrough(scroll_container)

        elif mode == "click":
            self.btn_click.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.tip_label.configure(text="Game Autoclicker selected. Configure settings in the tabs below.")

            scroll_container = self._create_config_scroll_container(self.right_frame)
            self._create_mode_banner(
                scroll_container,
                "Game Autoclicker",
                "Click at a fixed rate or react instantly when a target color appears on screen."
            )

            general_body = self._create_settings_section(scroll_container, "GENERAL")

            lbl_click = ctk.CTkLabel(general_body, text="Mouse Button:", font=("Segoe UI", 12, "bold"),
                                     text_color="#d0dbe5")
            lbl_click.pack(anchor="w", pady=(0, 6))

            self.combo_click_button = ctk.CTkOptionMenu(
                general_body, values=["Left Click", "Right Click", "Middle Click"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"click_button": choice}), self.save_config()]
            )
            self.combo_click_button.set(self.config_data.get("click_button", "Left Click"))
            self.combo_click_button.pack(fill="x")

            method_body = self._create_settings_section(scroll_container, "METHOD")
            self.click_tabs = ctk.CTkTabview(
                method_body, fg_color="#212b36", segmented_button_fg_color="#2a3543",
                segmented_button_selected_color="#1e90ff", segmented_button_selected_hover_color="#1872cc",
                segmented_button_unselected_color="#2a3543", segmented_button_unselected_hover_color="#364556",
                text_color="#ffffff"
            )
            self.click_tabs.pack(fill="x")
            self.click_tabs.add("Fixed Position")
            self.click_tabs.add("Color Scan")
            self.click_tabs.configure(command=self._on_click_tab_changed)

            fixed_tab = self.click_tabs.tab("Fixed Position")
            color_tab = self.click_tabs.tab("Color Scan")

            # --- Fixed Position tab ---
            speed_body = self._create_settings_section(fixed_tab, "SPEED")

            self.frame_click_speed = ctk.CTkFrame(speed_body, fg_color="transparent")
            self.frame_click_speed.pack(fill="x")
            self.frame_click_speed.grid_columnconfigure(0, weight=1)
            self.frame_click_speed.grid_rowconfigure(2, minsize=18)

            lbl_cps = ctk.CTkLabel(self.frame_click_speed, text="Clicks Per Second:", font=("Segoe UI", 12, "bold"),
                                   text_color="#d0dbe5")
            lbl_cps.grid(row=0, column=0, sticky="w", pady=(0, 4))

            cps = self.config_data.get("clicks_per_second", 10)
            interval_ms = int(1000 / max(1, cps))
            self.lbl_cps_value = ctk.CTkLabel(
                self.frame_click_speed,
                text=f"{cps} clicks/sec  ({interval_ms}ms interval)",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_cps_value.grid(row=1, column=0, sticky="w", pady=(0, 6))

            self.slider_cps = ctk.CTkSlider(
                self.frame_click_speed, from_=1, to=50, number_of_steps=49, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=self._update_cps_label
            )
            self.slider_cps.set(cps)
            self.slider_cps.grid(row=2, column=0, sticky="ew", pady=(0, 4))

            ctk.CTkLabel(fixed_tab, text="Clicks repeatedly at the current cursor position.",
                         font=("Segoe UI", 11), text_color="#8a99a8", wraplength=400, justify="left").pack(
                anchor="w", padx=4, pady=(4, 0))

            # --- Color Scan tab ---
            color_body = self._create_settings_section(color_tab, "TARGET COLOR")

            self.frame_color_target = ctk.CTkFrame(color_body, fg_color="transparent")
            self.frame_color_target.pack(fill="x", pady=(0, 12))

            lbl_color = ctk.CTkLabel(self.frame_color_target, text="Target Color (RGB):", font=("Segoe UI", 12, "bold"),
                                     text_color="#d0dbe5")
            lbl_color.pack(anchor="w", pady=(0, 6))

            color_row = ctk.CTkFrame(self.frame_color_target, fg_color="transparent")
            color_row.pack(fill="x")

            self.entry_color_r = ctk.CTkEntry(color_row, width=50, fg_color="#2a3543", border_color="#3a4959",
                                              text_color="#ffffff")
            self.entry_color_r.insert(0, str(self.config_data.get("target_color_r", 255)))
            self.entry_color_r.pack(side="left", padx=(0, 4))

            self.entry_color_g = ctk.CTkEntry(color_row, width=50, fg_color="#2a3543", border_color="#3a4959",
                                              text_color="#ffffff")
            self.entry_color_g.insert(0, str(self.config_data.get("target_color_g", 0)))
            self.entry_color_g.pack(side="left", padx=(0, 4))

            self.entry_color_b = ctk.CTkEntry(color_row, width=50, fg_color="#2a3543", border_color="#3a4959",
                                              text_color="#ffffff")
            self.entry_color_b.insert(0, str(self.config_data.get("target_color_b", 0)))
            self.entry_color_b.pack(side="left", padx=(0, 8))

            self.color_preview = ctk.CTkFrame(color_row, width=28, height=28, fg_color=self._rgb_to_hex(
                self.config_data.get("target_color_r", 255),
                self.config_data.get("target_color_g", 0),
                self.config_data.get("target_color_b", 0),
            ), corner_radius=4)
            self.color_preview.pack(side="left", padx=(0, 8))
            self.color_preview.pack_propagate(False)

            self.btn_pick_color = ctk.CTkButton(
                color_row, text="Pick from Screen", height=28, font=("Segoe UI", 11),
                fg_color="#2a3543", hover_color="#364556", border_width=1, border_color="#3a4959",
                command=self._start_color_pick
            )
            self.btn_pick_color.pack(side="left")

            self.frame_color_tolerance = ctk.CTkFrame(color_body, fg_color="transparent")
            self.frame_color_tolerance.pack(fill="x")
            self.frame_color_tolerance.grid_columnconfigure(0, weight=1)
            self.frame_color_tolerance.grid_rowconfigure(2, minsize=18)

            lbl_tol = ctk.CTkLabel(self.frame_color_tolerance, text="Color Tolerance:", font=("Segoe UI", 12, "bold"),
                                   text_color="#d0dbe5")
            lbl_tol.grid(row=0, column=0, sticky="w", pady=(0, 4))

            tol = self.config_data.get("color_tolerance", 10)
            self.lbl_tolerance_value = ctk.CTkLabel(
                self.frame_color_tolerance, text=f"{tol} (higher = more flexible match)",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_tolerance_value.grid(row=1, column=0, sticky="w", pady=(0, 6))

            self.slider_tolerance = ctk.CTkSlider(
                self.frame_color_tolerance, from_=0, to=50, number_of_steps=50, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=self._update_tolerance_label
            )
            self.slider_tolerance.set(tol)
            self.slider_tolerance.grid(row=2, column=0, sticky="ew", pady=(0, 4))

            scan_body = self._create_settings_section(color_tab, "SCAN REGION")

            self.frame_scan_region_select = ctk.CTkFrame(scan_body, fg_color="transparent")
            self.frame_scan_region_select.pack(fill="x")

            lbl_region = ctk.CTkLabel(self.frame_scan_region_select, text="Region Type:", font=("Segoe UI", 12, "bold"),
                                      text_color="#d0dbe5")
            lbl_region.pack(anchor="w", pady=(0, 6))

            self.combo_scan_region = ctk.CTkOptionMenu(
                self.frame_scan_region_select, values=["Full Screen", "Around Cursor", "Custom Region"],
                fg_color="#2a3543", button_color="#1e90ff", button_hover_color="#1872cc",
                text_color="#ffffff", dropdown_fg_color="#212b36", dropdown_text_color="#ffffff",
                command=lambda choice: [self.config_data.update({"scan_region": choice}), self.save_config(),
                                        self._toggle_scan_region_view(choice)]
            )
            self.combo_scan_region.set(self.config_data.get("scan_region", "Full Screen"))
            self.combo_scan_region.pack(fill="x")

            self.frame_scan_around = ctk.CTkFrame(scan_body, fg_color="transparent")
            self.frame_scan_around.pack(fill="x", pady=(12, 0))
            self.frame_scan_around.grid_columnconfigure(0, weight=1)
            self.frame_scan_around.grid_rowconfigure(2, minsize=18)

            lbl_radius = ctk.CTkLabel(self.frame_scan_around, text="Scan Radius (Around Cursor):",
                                      font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_radius.grid(row=0, column=0, sticky="w", pady=(0, 4))
            self.lbl_scan_radius = lbl_radius

            radius = self.config_data.get("scan_radius", 200)
            self.lbl_radius_value = ctk.CTkLabel(
                self.frame_scan_around, text=f"{radius} px around cursor",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_radius_value.grid(row=1, column=0, sticky="w", pady=(0, 6))

            self.slider_scan_radius = ctk.CTkSlider(
                self.frame_scan_around, from_=50, to=800, number_of_steps=750, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_radius_value.configure(text=f"{int(v)} px around cursor"),
                                   self.config_data.update({"scan_radius": int(v)}), self.save_config()]
            )
            self.slider_scan_radius.set(radius)
            self.slider_scan_radius.grid(row=2, column=0, sticky="ew", pady=(0, 4))

            self.frame_scan_custom = ctk.CTkFrame(scan_body, fg_color="transparent")
            self.frame_scan_custom.pack(fill="x", pady=(12, 0))

            lbl_custom = ctk.CTkLabel(self.frame_scan_custom, text="Custom Region",
                                    font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_custom.pack(anchor="w", pady=(0, 8))
            self.lbl_scan_custom = lbl_custom

            custom_grid = ctk.CTkFrame(self.frame_scan_custom, fg_color="transparent")
            custom_grid.pack(fill="x")
            custom_grid.grid_columnconfigure(1, weight=1, uniform="entry")
            custom_grid.grid_columnconfigure(3, weight=1, uniform="entry")

            region_fields = [
                (0, "X:", "scan_x", 0),
                (0, "Y:", "scan_y", 0),
                (1, "Width:", "scan_width", 800),
                (1, "Height:", "scan_height", 600),
            ]
            for row, label_text, attr, default in region_fields:
                col = 0 if label_text in ("X:", "Width:") else 2
                pad_right = 20 if col == 0 else 0

                ctk.CTkLabel(
                    custom_grid, text=label_text, width=54, anchor="w",
                    font=("Segoe UI", 12), text_color="#8a99a8"
                ).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)

                entry = ctk.CTkEntry(
                    custom_grid, height=32, fg_color="#2a3543", border_color="#3a4959", text_color="#ffffff"
                )
                entry.insert(0, str(self.config_data.get(attr, default)))
                entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, pad_right), pady=4)
                setattr(self, f"entry_{attr}", entry)

            self.btn_pick_region = ctk.CTkButton(
                self.frame_scan_custom, text="Select Region on Screen", height=32, font=("Segoe UI", 12),
                fg_color="#2a3543", hover_color="#364556", border_width=1, border_color="#3a4959",
                command=self._start_region_pick
            )
            self.btn_pick_region.pack(fill="x", pady=(10, 0))

            timing_body = self._create_settings_section(color_tab, "SCAN TIMING")

            self.frame_scan_timing = ctk.CTkFrame(timing_body, fg_color="transparent")
            self.frame_scan_timing.pack(fill="x")
            self.frame_scan_timing.grid_columnconfigure(0, weight=1)
            self.frame_scan_timing.grid_rowconfigure(2, minsize=18)
            self.frame_scan_timing.grid_rowconfigure(5, minsize=18)

            lbl_scan_rate = ctk.CTkLabel(self.frame_scan_timing, text="Scan Rate:", font=("Segoe UI", 12, "bold"),
                                         text_color="#d0dbe5")
            lbl_scan_rate.grid(row=0, column=0, sticky="w", pady=(0, 4))

            scan_rate = self.config_data.get("scan_rate", 30)
            self.lbl_scan_rate_value = ctk.CTkLabel(
                self.frame_scan_timing, text=f"{scan_rate} scans/sec",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_scan_rate_value.grid(row=1, column=0, sticky="w", pady=(0, 6))

            self.slider_scan_rate = ctk.CTkSlider(
                self.frame_scan_timing, from_=1, to=60, number_of_steps=59, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=lambda v: [self.lbl_scan_rate_value.configure(text=f"{int(v)} scans/sec"),
                                   self.config_data.update({"scan_rate": int(v)}), self.save_config()]
            )
            self.slider_scan_rate.set(scan_rate)
            self.slider_scan_rate.grid(row=2, column=0, sticky="ew", pady=(0, 10))

            lbl_cooldown = ctk.CTkLabel(self.frame_scan_timing, text="Click Cooldown (max CPS):",
                                        font=("Segoe UI", 12, "bold"), text_color="#d0dbe5")
            lbl_cooldown.grid(row=3, column=0, sticky="w", pady=(0, 4))

            self.lbl_scan_cps_value = ctk.CTkLabel(
                self.frame_scan_timing, text=f"{cps} clicks/sec max after detection",
                font=("Segoe UI", 11, "italic"), text_color="#8a99a8"
            )
            self.lbl_scan_cps_value.grid(row=4, column=0, sticky="w", pady=(0, 6))

            self.slider_scan_cps = ctk.CTkSlider(
                self.frame_scan_timing, from_=1, to=50, number_of_steps=49, height=16,
                fg_color="#2a3543", progress_color="#1e90ff", button_color="#1e90ff",
                command=self._update_scan_cps_label
            )
            self.slider_scan_cps.set(cps)
            self.slider_scan_cps.grid(row=5, column=0, sticky="ew", pady=(0, 4))

            initial_click_mode = self.config_data.get("click_mode", "Fixed Position")
            self.click_tabs.set("Color Scan" if initial_click_mode == "Color Scan" else "Fixed Position")
            self._toggle_scan_region_view(self.config_data.get("scan_region", "Full Screen"))
            self._apply_slider_scroll_passthrough(scroll_container)

        elif mode == "teams":
            self.btn_teams.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            scroll_container = self._create_config_scroll_container(self.right_frame)
            self._create_mode_banner(
                scroll_container,
                "Smart Teams",
                "Automated Teams presence and activity. Settings will appear here when this module is ready."
            )
            coming_body = self._create_settings_section(scroll_container, "STATUS")
            ctk.CTkLabel(
                coming_body, text="This module is still in development.",
                font=("Segoe UI", 12), text_color="#5f758a"
            ).pack(anchor="w")
            self.tip_label.configure(text="Smart Teams selected. Module coming soon.")

        elif mode == "macro":
            self.btn_macro.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            scroll_container = self._create_config_scroll_container(self.right_frame)
            self._create_mode_banner(
                scroll_container,
                "Macro Recorder",
                "Record and replay mouse and keyboard sequences. Settings will appear here when this module is ready."
            )
            coming_body = self._create_settings_section(scroll_container, "STATUS")
            ctk.CTkLabel(
                coming_body, text="This module is still in development.",
                font=("Segoe UI", 12), text_color="#5f758a"
            ).pack(anchor="w")
            self.tip_label.configure(text="Macro Recorder selected. Module coming soon.")

        # Light up the START button, ensure STOP is dimmed
        self.btn_start.configure(
            state="normal",
            fg_color="#1b5e3a", text_color="#a3e2bc", hover_color="#227a4b", border_color="#2b8c56"
        )
        self.btn_stop.configure(
            state="disabled",
            fg_color="#2a3543", text_color="#5f758a", hover_color="#2a3543", border_color="#3a4959"
        )

    def _create_config_scroll_container(self, parent):
        scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color="#2a3543",
            scrollbar_button_hover_color="#364556",
        )
        scroll.pack(fill="both", expand=True, padx=16, pady=14)
        return scroll

    def _scroll_settings_panel(self, scroll_container, event):
        canvas = scroll_container._parent_canvas
        if canvas.yview() == (0.0, 1.0):
            return

        if sys.platform.startswith("win"):
            canvas.yview("scroll", -int(event.delta / 6), "units")
        elif sys.platform == "darwin":
            canvas.yview("scroll", -event.delta, "units")
        else:
            canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def _bind_slider_scroll_passthrough(self, slider, scroll_container):
        def forward_wheel(event):
            self._scroll_settings_panel(scroll_container, event)
            return "break"

        slider._canvas.unbind("<MouseWheel>")
        slider._canvas.bind("<MouseWheel>", forward_wheel)
        if "linux" in sys.platform:
            slider._canvas.unbind("<Button-4>")
            slider._canvas.unbind("<Button-5>")
            slider._canvas.bind("<Button-4>", forward_wheel)
            slider._canvas.bind("<Button-5>", forward_wheel)

    def _apply_slider_scroll_passthrough(self, scroll_container, parent=None):
        if parent is None:
            parent = scroll_container

        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkSlider):
                self._bind_slider_scroll_passthrough(child, scroll_container)
            elif child.winfo_children():
                self._apply_slider_scroll_passthrough(scroll_container, child)

    def _create_mode_banner(self, parent, title, description):
        banner = ctk.CTkFrame(parent, fg_color="#1a222d", corner_radius=8, border_width=1, border_color="#2d3945")
        banner.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(banner, text=title, font=("Segoe UI", 13, "bold"), text_color="#ffffff").pack(
            anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(banner, text=description, font=("Segoe UI", 11), text_color="#8a99a8",
                     wraplength=420, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

    def _create_subsection_label(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, font=("Segoe UI", 11, "bold"), text_color="#5f758a")
        lbl.pack(anchor="w", pady=(12, 6))
        return lbl

    def _disabled_palette(self):
        return {"text": "#5f758a", "accent": "#3a4959"}

    def _create_settings_section(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="#1a222d", corner_radius=8, border_width=1, border_color="#2d3945")
        card.pack(fill="x", pady=(0, 14))

        header = ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color="#8a99a8")
        header.pack(anchor="w", padx=16, pady=(14, 10))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(0, 14))
        return body

    # --- UI HELPER METHODS FOR DYNAMIC VIEWPORTS ---
    def _update_cps_label(self, value):
        cps = int(value)
        interval_ms = int(1000 / max(1, cps))
        self.lbl_cps_value.configure(text=f"{cps} clicks/sec  ({interval_ms}ms interval)")
        self.config_data.update({"clicks_per_second": cps})
        self.save_config()

    def _update_scan_cps_label(self, value):
        cps = int(value)
        self.lbl_scan_cps_value.configure(text=f"{cps} clicks/sec max after detection")
        self.config_data.update({"clicks_per_second": cps})
        self.save_config()

    def _update_tolerance_label(self, value):
        tol = int(value)
        self.lbl_tolerance_value.configure(text=f"{tol} (higher = more flexible match)")
        self.config_data.update({"color_tolerance": tol})
        self.save_config()

    def _rgb_to_hex(self, r, g, b):
        return f"#{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"

    def _update_color_preview(self):
        try:
            r = int(self.entry_color_r.get())
            g = int(self.entry_color_g.get())
            b = int(self.entry_color_b.get())
            self.color_preview.configure(fg_color=self._rgb_to_hex(r, g, b))
            self.config_data.update({"target_color_r": r, "target_color_g": g, "target_color_b": b})
            self.save_config()
        except ValueError:
            pass

    def _start_color_pick(self):
        self._color_pick_countdown = 3
        self.tip_label.configure(text="Move mouse to target color... 3", text_color="#1e90ff")
        self._tick_color_pick()

    def _tick_color_pick(self):
        self._color_pick_countdown -= 1
        if self._color_pick_countdown > 0:
            self.tip_label.configure(text=f"Move mouse to target color... {self._color_pick_countdown}",
                                     text_color="#1e90ff")
            self.after(1000, self._tick_color_pick)
        else:
            self._capture_pixel_color()

    def _capture_pixel_color(self):
        import pyautogui
        x, y = pyautogui.position()
        r, g, b = pyautogui.pixel(x, y)
        self.entry_color_r.delete(0, "end")
        self.entry_color_g.delete(0, "end")
        self.entry_color_b.delete(0, "end")
        self.entry_color_r.insert(0, str(r))
        self.entry_color_g.insert(0, str(g))
        self.entry_color_b.insert(0, str(b))
        self._update_color_preview()
        self.tip_label.configure(text=f"Color picked: RGB({r}, {g}, {b})", text_color="#2ed573")

    def _set_scan_region_entries(self, x, y, width, height):
        for entry, value in (
            (self.entry_scan_x, x),
            (self.entry_scan_y, y),
            (self.entry_scan_width, width),
            (self.entry_scan_height, height),
        ):
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, str(value))

        self.config_data.update({
            "scan_region": "Custom Region",
            "scan_x": x,
            "scan_y": y,
            "scan_width": width,
            "scan_height": height,
        })
        self.combo_scan_region.set("Custom Region")
        self._toggle_scan_region_view("Custom Region")
        self.save_config()

    def _start_region_pick(self):
        if self.is_running or self._region_picker is not None:
            return

        self.tip_label.configure(
            text="Select scan region: drag a rectangle on screen (Esc to cancel)",
            text_color="#1e90ff",
        )
        self.update_idletasks()
        self.withdraw()
        self.after(200, self._open_region_picker)

    def _open_region_picker(self):
        self._region_picker = RegionPickerOverlay(
            self,
            on_complete=self._on_region_pick_complete,
            on_cancel=self._on_region_pick_cancel,
        )
        self._region_picker.open()

    def _finish_region_pick_ui(self):
        self._region_picker = None
        if self.winfo_exists():
            self.deiconify()
            self.lift()
            self.focus_force()

    def _on_region_pick_complete(self, x, y, width, height):
        self.after(0, lambda: self._apply_region_pick_result(x, y, width, height))

    def _apply_region_pick_result(self, x, y, width, height):
        self._finish_region_pick_ui()
        if not hasattr(self, "entry_scan_x"):
            return
        self._set_scan_region_entries(x, y, width, height)
        self.tip_label.configure(
            text=f"Scan region set: {width}×{height} at ({x}, {y})",
            text_color="#2ed573",
        )

    def _on_region_pick_cancel(self):
        self.after(0, self._apply_region_pick_cancel)

    def _apply_region_pick_cancel(self):
        self._finish_region_pick_ui()
        self.tip_label.configure(text="Region selection cancelled.", text_color="#8a99a8")

    def _on_click_tab_changed(self):
        tab = self.click_tabs.get()
        mode = "Color Scan" if tab == "Color Scan" else "Fixed Position"
        self.config_data.update({"click_mode": mode})
        self.save_config()

    def _toggle_scan_region_view(self, choice):
        disabled = self._disabled_palette()
        active = {"accent": "#1e90ff", "btn": "#1e90ff", "text": "#8a99a8", "label": "#d0dbe5", "entry": "#ffffff"}

        if choice == "Around Cursor":
            self.slider_scan_radius.configure(state="normal", progress_color=active["accent"], button_color=active["btn"])
            self.lbl_radius_value.configure(text_color=active["text"])
            self.lbl_scan_radius.configure(text_color=active["label"])
            self.lbl_scan_custom.configure(text_color=disabled["text"])
            self.btn_pick_region.configure(state="normal")
            for entry in (self.entry_scan_x, self.entry_scan_y, self.entry_scan_width, self.entry_scan_height):
                entry.configure(state="disabled", text_color=disabled["text"])
        elif choice == "Custom Region":
            self.slider_scan_radius.configure(state="disabled", progress_color=disabled["accent"], button_color=disabled["text"])
            self.lbl_radius_value.configure(text_color=disabled["text"])
            self.lbl_scan_radius.configure(text_color=disabled["text"])
            self.lbl_scan_custom.configure(text_color=active["label"])
            self.btn_pick_region.configure(state="normal")
            for entry in (self.entry_scan_x, self.entry_scan_y, self.entry_scan_width, self.entry_scan_height):
                entry.configure(state="normal", text_color=active["entry"])
        else:
            self.slider_scan_radius.configure(state="disabled", progress_color=disabled["accent"], button_color=disabled["text"])
            self.lbl_radius_value.configure(text_color=disabled["text"])
            self.lbl_scan_radius.configure(text_color=disabled["text"])
            self.lbl_scan_custom.configure(text_color=disabled["text"])
            self.btn_pick_region.configure(state="normal")
            for entry in (self.entry_scan_x, self.entry_scan_y, self.entry_scan_width, self.entry_scan_height):
                entry.configure(state="disabled", text_color=disabled["text"])

    def _toggle_ghost_view(self):
        enabled = self.switch_process_ghost.get()
        disabled = self._disabled_palette()

        if enabled:
            self.lbl_ghost.configure(text_color="#d0dbe5")
            self.combo_ghost_process.configure(state="normal", text_color="#ffffff", button_color="#1e90ff")
        else:
            self.lbl_ghost.configure(text_color=disabled["text"])
            self.combo_ghost_process.configure(state="disabled", text_color=disabled["text"], button_color=disabled["accent"])

        self.config_data.update({"use_process_ghost": enabled})
        self.save_config()

    def _toggle_sleep_strategy_view(self, choice):
        disabled = self._disabled_palette()
        is_keyboard = choice == "Keyboard Key Strike"

        if is_keyboard:
            self.lbl_key.configure(text_color="#d0dbe5")
            self.combo_key.configure(state="normal", text_color="#ffffff", button_color="#1e90ff")
            self.lbl_pixels.configure(text_color=disabled["text"])
            self.slider_pixels.configure(state="disabled", progress_color=disabled["accent"], button_color=disabled["text"])
        else:
            self.lbl_key.configure(text_color=disabled["text"])
            self.combo_key.configure(state="disabled", text_color=disabled["text"], button_color=disabled["accent"])
            self.lbl_pixels.configure(text_color="#d0dbe5")
            self.slider_pixels.configure(state="normal", progress_color="#1e90ff", button_color="#1e90ff")

    def _toggle_jitter_view(self):
        enabled = self.switch_random.get()
        disabled = self._disabled_palette()

        if enabled:
            self.slider_time.configure(state="disabled", progress_color=disabled["accent"], button_color=disabled["text"])
            self.lbl_time_value.configure(text_color=disabled["text"])
            self.lbl_rand_title.configure(text_color="#d0dbe5")
            self.entry_min.configure(state="normal", text_color="#ffffff")
            self.entry_max.configure(state="normal", text_color="#ffffff")
        else:
            self.slider_time.configure(state="normal", progress_color="#1e90ff", button_color="#1e90ff")
            self.lbl_time_value.configure(text_color="#8a99a8")
            self.lbl_rand_title.configure(text_color=disabled["text"])
            self.entry_min.configure(state="disabled", text_color=disabled["text"])
            self.entry_max.configure(state="disabled", text_color=disabled["text"])

        self.config_data.update({"use_jitter": enabled})
        self.save_config()

    def _toggle_smart_idle_view(self):
        enabled = self.switch_smart_idle.get()
        disabled = self._disabled_palette()
        state = "normal" if enabled else "disabled"
        accent = "#1e90ff" if enabled else disabled["accent"]
        btn = "#1e90ff" if enabled else disabled["text"]
        text = "#8a99a8" if enabled else disabled["text"]

        self.slider_idle_threshold.configure(state=state, progress_color=accent, button_color=btn)
        self.lbl_idle_value.configure(text_color=text)
        if hasattr(self, "lbl_idle"):
            self.lbl_idle.configure(text_color="#d0dbe5" if enabled else disabled["text"])

        self.config_data.update({"use_smart_idle": enabled})
        self.save_config()
        self.after(10, self._refresh_idle_slider)

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

            worker_config = {
                "strategy": strategy,
                "key_to_strike": key_to_strike,
                "pixel_distance": pixel_distance,
                "time_interval": time_interval,
                "use_jitter": use_jitter,
                "use_smart_idle": use_smart_idle,
                "idle_threshold": idle_threshold,
                "time_min": time_min,
                "time_max": time_max,
            }

            use_process_ghost = self.switch_process_ghost.get()
            ghost_name = self.combo_ghost_process.get()

            self.switch_process_ghost.configure(state="disabled", text_color=disabled_text, progress_color=disabled_accent)
            self.combo_ghost_process.configure(state="disabled", text_color=disabled_text, button_color=disabled_accent)

            if use_process_ghost:
                self.process_ghost = ProcessGhost(self)
                self.process_ghost.activate(ghost_name)

                if self.process_ghost.start_disguised_worker(ghost_name, worker_config):
                    self.tip_label.configure(
                        text=f"STATUS: RUNNING 🚀 (Anti-Sleep active as {ghost_name})",
                        text_color="#2ed573"
                    )
                else:
                    self.sleep_worker = AntiSleepWorker(**worker_config)
                    self.sleep_worker.start()
                    if not is_frozen():
                        self.tip_label.configure(
                            text="STATUS: RUNNING 🚀 (Window disguised — build as .exe for Task Manager disguise)",
                            text_color="#2ed573"
                        )
            else:
                self.sleep_worker = AntiSleepWorker(**worker_config)
                self.sleep_worker.start()

        elif self.selected_mode == "click":
            click_button = self.combo_click_button.get()
            click_mode = "Color Scan" if self.click_tabs.get() == "Color Scan" else "Fixed Position"
            clicks_per_second = int(self.slider_cps.get()) if click_mode == "Fixed Position" else int(self.slider_scan_cps.get())

            disabled_text = "#5f758a"
            disabled_accent = "#3a4959"

            self.click_tabs.configure(state="disabled")
            self.combo_click_button.configure(state="disabled", text_color=disabled_text, button_color=disabled_accent)

            worker_kwargs = {
                "click_button": click_button,
                "clicks_per_second": clicks_per_second,
                "click_mode": click_mode,
            }

            if click_mode == "Color Scan":
                try:
                    target_color = (
                        int(self.entry_color_r.get()),
                        int(self.entry_color_g.get()),
                        int(self.entry_color_b.get()),
                    )
                except ValueError:
                    target_color = (255, 0, 0)

                try:
                    scan_x = int(self.entry_scan_x.get())
                    scan_y = int(self.entry_scan_y.get())
                    scan_width = int(self.entry_scan_width.get())
                    scan_height = int(self.entry_scan_height.get())
                except ValueError:
                    scan_x, scan_y, scan_width, scan_height = 0, 0, 800, 600

                worker_kwargs.update({
                    "target_color": target_color,
                    "color_tolerance": int(self.slider_tolerance.get()),
                    "scan_region": self.combo_scan_region.get(),
                    "scan_radius": int(self.slider_scan_radius.get()),
                    "scan_x": scan_x,
                    "scan_y": scan_y,
                    "scan_width": scan_width,
                    "scan_height": scan_height,
                    "scan_rate": int(self.slider_scan_rate.get()),
                })

                self.slider_tolerance.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
                self.slider_scan_radius.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
                self.slider_scan_rate.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
                self.slider_scan_cps.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
                self.combo_scan_region.configure(state="disabled", text_color=disabled_text, button_color=disabled_accent)
                self.entry_color_r.configure(state="disabled", text_color=disabled_text)
                self.entry_color_g.configure(state="disabled", text_color=disabled_text)
                self.entry_color_b.configure(state="disabled", text_color=disabled_text)
                self.btn_pick_color.configure(state="disabled")
                self.btn_pick_region.configure(state="disabled")
                self.entry_scan_x.configure(state="disabled", text_color=disabled_text)
                self.entry_scan_y.configure(state="disabled", text_color=disabled_text)
                self.entry_scan_width.configure(state="disabled", text_color=disabled_text)
                self.entry_scan_height.configure(state="disabled", text_color=disabled_text)
                self.lbl_tolerance_value.configure(text_color=disabled_text)
                self.lbl_scan_rate_value.configure(text_color=disabled_text)
                self.lbl_scan_cps_value.configure(text_color=disabled_text)
                self.lbl_radius_value.configure(text_color=disabled_text)

                self.tip_label.configure(
                    text=f"STATUS: COLOR SCAN ACTIVE — hunting RGB{target_color}",
                    text_color="#2ed573"
                )
            else:
                self.slider_cps.configure(state="disabled", progress_color=disabled_accent, button_color=disabled_text)
                self.lbl_cps_value.configure(text_color=disabled_text)

            self.click_worker = AutoClickWorker(**worker_kwargs)
            self.click_worker.start()

    def stop_action(self):
        self.is_running = False
        self.btn_stop.configure(state="disabled")
        self.btn_start.configure(state="normal")

        if self.sleep_worker:
            self.sleep_worker.stop()
            self.sleep_worker = None

        if self.click_worker:
            self.click_worker.stop()
            self.click_worker = None

        if self.process_ghost:
            self.process_ghost.stop_disguised_worker()
            self.process_ghost.deactivate()
            self.process_ghost = None

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
                    self.config_data["use_process_ghost"] = bool(self.config_data.get("use_process_ghost", False))
            except Exception as e:
                print(f"[ERROR] Failed to load local configuration file: {e}")

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, "w") as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save configuration layout state: {e}")