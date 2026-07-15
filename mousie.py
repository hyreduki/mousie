import customtkinter as ctk
import requests
import threading

# Forceer direct de Dark Mode voor die strakke look
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class MousieApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.CURRENT_VERSION = "1.0.0"
        self.UPDATE_URL = "https://api.github.com/repos/hyreduki/mousie/releases/latest"

        # Venster breder gemaakt (850px) om plaats te maken voor het rechterpaneel
        self.title("MOUSIE v1.0.0")
        self.geometry("850x450") 
        self.resizable(False, False)
        
        # Diepe donkere Windows 11 kleur voor de achtergrond
        self.configure(fg_color="#1a222d")

        self.selected_mode = None
        self.is_running = False

        self.setup_ui()
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def setup_ui(self):
        # Main title display across the top width
        self.title_label = ctk.CTkLabel(self, text="MOUSIE AUTOMATION PLATFORM", font=("Segoe UI", 16, "bold"), text_color="#ffffff")
        self.title_label.pack(pady=(15, 5))

        # Main horizontal split container for left and right viewports
        self.main_split_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split_container.pack(pady=5, padx=20, fill="both", expand=True)

        # ==========================================
        # LEFT VIEWPORT: MODE SELECTION (Fixed width: 390px)
        # ==========================================
        self.left_frame = ctk.CTkFrame(self.main_split_container, width=390, corner_radius=10, fg_color="#212b36", border_width=1, border_color="#2d3945")
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        self.left_frame.pack_propagate(False) # Prevents layout shifting from child widget dimensions

        self.left_title = ctk.CTkLabel(self.left_frame, text="Select Mode", font=("Segoe UI", 13, "bold"), text_color="#8a99a8")
        self.left_title.pack(pady=(10, 5))

        # Standard dictionary layout settings for core execution buttons
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

        self.btn_sleep = ctk.CTkButton(**button_args, text="🧠  Anti-Sleep Mode", command=lambda: self.select_mode("sleep"))
        self.btn_sleep.pack(pady=6, padx=15, fill="x")

        self.btn_click = ctk.CTkButton(**button_args, text="🎮  Game Autoclicker", command=lambda: self.select_mode("click"))
        self.btn_click.pack(pady=6, padx=15, fill="x")

        self.btn_teams = ctk.CTkButton(**button_args, text="🤝  Smart Teams Mode", command=lambda: self.select_mode("teams"))
        self.btn_teams.pack(pady=6, padx=15, fill="x")

        self.btn_macro = ctk.CTkButton(**button_args, text="🎥  Macro Mode (Record/Play)", command=lambda: self.select_mode("macro"))
        self.btn_macro.pack(pady=6, padx=15, fill="x")

        # ==========================================
        # RIGHT VIEWPORT: CONFIG PANEL (Fixed width: 390px)
        # ==========================================
        self.right_frame = ctk.CTkFrame(self.main_split_container, width=390, corner_radius=10, fg_color="#212b36", border_width=1, border_color="#2d3945")
        self.right_frame.pack(side="right", fill="both", expand=False, padx=(10, 0))
        self.right_frame.pack_propagate(False) # Prevents layout shifting from child widget dimensions

        self.right_title = ctk.CTkLabel(self.right_frame, text="Configuration & Status", font=("Segoe UI", 13, "bold"), text_color="#8a99a8")
        self.right_title.pack(pady=(10, 5))

        # Content status label configured with auto-wrapping for text boundaries
        self.config_placeholder_label = ctk.CTkLabel(
            self.right_frame, 
            text="Select a mode to configure / start", 
            font=("Segoe UI", 13), 
            text_color="#5f758a",
            wraplength=350,
            justify="center"
        )
        self.config_placeholder_label.pack(expand=True, fill="both", padx=15)

        # ==========================================
        # BOTTOM CONTROLS & SYSTEM FEEDBACK LINE
        # ==========================================
        self.tip_label = ctk.CTkLabel(self, text="Please select a mode from the left panel to begin.", font=("Segoe UI", 11, "italic"), text_color="#8a99a8")
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

    # --- LIVE GITHUB UPDATE LOGIC ---
    def check_for_updates(self):
        try:
            response = requests.get(self.UPDATE_URL, timeout=5)
            if response.status_code == 404: return
            github_data = response.json()
            latest_version = github_data["tag_name"].lower().replace("v", "") 
            if latest_version != self.CURRENT_VERSION:
                if github_data["assets"]:
                    self.after(0, lambda: self.show_update_popup(latest_version, github_data))
        except Exception as e:
            print(f"Update verification sequence failed: {e}")

    def show_update_popup(self, new_version, github_data):
        popup = ctk.CTkToplevel(self)
        popup.title("Update Available!")
        popup.geometry("380x200")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)

        msg_label = ctk.CTkLabel(popup, text=f"A new version is available on GitHub!\n\nCurrent version: v{self.CURRENT_VERSION}\nLatest version: v{new_version}", font=("Arial", 13, "bold"))
        msg_label.pack(pady=25)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        download_url = github_data["assets"][0]["browser_download_url"]

        btn_update = ctk.CTkButton(btn_frame, text="Download Now 🚀", fg_color="#1e90ff", font=("Arial", 12, "bold"), command=lambda: self.trigger_actual_download(popup, download_url))
        btn_update.pack(side="left", expand=True, padx=5)

        btn_later = ctk.CTkButton(btn_frame, text="Later", fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), command=popup.destroy)
        btn_later.pack(side="right", expand=True, padx=5)

    def trigger_actual_download(self, popup_window, download_url):
        popup_window.destroy()
        self.tip_label.configure(text="Downloading new deployment asset from GitHub... ⏳", text_color="#1e90ff")
        threading.Thread(target=self.download_installer_worker, args=(download_url,), daemon=True).start()

    def download_installer_worker(self, url):
        try:
            import os
            import subprocess
            filename = url.split("/")[-1]
            download_path = os.path.join(os.environ['TEMP'], filename)
            r = requests.get(url, stream=True)
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            self.tip_label.configure(text="Download complete! Initializing setup installation process...", text_color="#2ed573")
            subprocess.Popen([download_path], shell=True)
            self.quit()
        except Exception as e:
            self.tip_label.configure(text=f"Download transaction routine failed: {e}", text_color="#ff4757")

    # --- STANDARD UX CONTEXT LOGIC ---
    def select_mode(self, mode):
        if self.is_running: return
        self.selected_mode = mode
        default_bg, default_text = ("#2a3543", "#d0dbe5")
        self.btn_sleep.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_click.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_teams.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")
        self.btn_macro.configure(fg_color=default_bg, text_color=default_text, border_color="#3a4959")

        # Hier passen we dynamisch de tekst aan de rechterkant aan op basis van de gekozen modus
        if mode == "sleep":
            self.btn_sleep.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.config_placeholder_label.configure(text="🧠 Anti-Sleep Mode Configuration\n\nThis mode simulates microscopic cursor shifts\nto keep your operating system awake natively.\nNo artificial mouse clicks are triggered.\n\nReady to activate.", text_color="#ffffff")
            self.tip_label.configure(text="Anti-Sleep Mode selected. Press F7 or click START.")
        elif mode == "click":
            self.btn_click.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.config_placeholder_label.configure(text="🎮 Game Autoclicker Configuration\n\nTriggers ultra-high frequency clicks at your\ncurrent cursor location. Ideal for gaming inputs.\n\n[Settings inputs will be placed here]", text_color="#ffffff")
            self.tip_label.configure(text="Game Autoclicker selected. Press F7 or click START.")
        elif mode == "teams":
            self.btn_teams.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.config_placeholder_label.configure(text="🤝 Smart Teams Mode Configuration\n\nSimulates authentic, human-like workflow activity\nto safely maintain active presence statuses\nacross corporate messaging clients.\n\nReady to activate.", text_color="#ffffff")
            self.tip_label.configure(text="Smart Teams Mode selected. Press F7 or click START.")
        elif mode == "macro":
            self.btn_macro.configure(fg_color="#1a3d54", text_color="#ffffff", border_color="#1e90ff")
            self.config_placeholder_label.configure(text="🎥 Macro Recorder Configuration\n\nRecord complex mouse trajectories and keyboard\nstrokes to loop them automatically.\n\n[Macro tools will be placed here]", text_color="#ffffff")
            self.tip_label.configure(text="Macro Recorder selected.")

        self.btn_start.configure(state="normal")

    def start_action(self):
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.tip_label.configure(text=f"STATUS: RUNNING 🚀 ({self.selected_mode.upper()} ACTIVE)", text_color="#2ed573")

    def stop_action(self):
        self.is_running = False
        self.btn_stop.configure(state="disabled")
        self.btn_start.configure(state="normal")
        self.select_mode(self.selected_mode)

if __name__ == "__main__":
    app = MousieApp()
    app.mainloop()
