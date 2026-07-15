import customtkinter as ctk
import requests
import threading

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

class SuperClickerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Local application version
        self.CURRENT_VERSION = "1.0.0"
        
        # Public GitHub API URL for tracking live releases
        self.UPDATE_URL = "https://api.github.com/repos/hyreduki/mousie/releases/latest"

        # Window configuration
        self.title("SUPER CLICKER PRO v2.1")
        self.geometry("500x550")
        self.resizable(False, False)

        self.selected_mode = None
        self.is_running = False

        # --- SETUP INTERFACE ---
        self.setup_ui()

        # --- AUTO-UPDATE CHECK ---
        # Executed in a separate thread to prevent the GUI from stuttering on startup
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def setup_ui(self):
        # Settings cog (top right)
        self.settings_button = ctk.CTkButton(self, text="⚙️", width=35, height=35, font=("Arial", 16), fg_color="transparent", command=self.open_settings)
        self.settings_button.place(x=450, y=10)

        # Main Title
        self.title_label = ctk.CTkLabel(self, text="MODE SELECTION", font=("Arial", 16, "bold"), text_color=("#1e90ff", "#70a1ff"))
        self.title_label.pack(pady=(20, 15))

        # Mode Selection Panel Container
        self.mode_frame = ctk.CTkFrame(self, corner_radius=12)
        self.mode_frame.pack(pady=10, padx=30, fill="both", expand=True)

        # 1. Anti-Sleep Mode Panel
        self.btn_sleep = ctk.CTkButton(self.mode_frame, text="🧠  Anti-Sleep Mode", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("sleep"))
        self.btn_sleep.pack(pady=8, padx=20, fill="x")

        # 2. Game Autoclicker Panel
        self.btn_click = ctk.CTkButton(self.mode_frame, text="🎮  Game Autoclicker", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("click"))
        self.btn_click.pack(pady=8, padx=20, fill="x")

        # 3. Smart Teams Mode Panel
        self.btn_teams = ctk.CTkButton(self.mode_frame, text="🤝  Smart Teams Mode", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("teams"))
        self.btn_teams.pack(pady=8, padx=20, fill="x")

        # 4. Macro Mode Panel
        self.btn_macro = ctk.CTkButton(self.mode_frame, text="🎥  Macro Mode (Record/Play)", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("macro"))
        self.btn_macro.pack(pady=8, padx=20, fill="x")

        # Context-aware status/help label
        self.tip_label = ctk.CTkLabel(self, text="Please select a mode below to begin.", font=("Arial", 12, "italic"), text_color="gray")
        self.tip_label.pack(pady=10)

        # Main Control Action Layout
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=(10, 25), padx=30, fill="x")

        self.btn_start = ctk.CTkButton(self.control_frame, text="▶  START", height=50, fg_color=("#2ed573", "#26af5f"), font=("Arial", 14, "bold"), state="disabled", command=self.start_action)
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(self.control_frame, text="■  STOP", height=50, fg_color=("#ff4757", "#ff6b81"), font=("Arial", 14, "bold"), state="disabled", command=self.stop_action)
        self.btn_stop.pack(side="right", padx=5, expand=True, fill="x")

    # --- LIVE GITHUB UPDATE LOGIC ---
    def check_for_updates(self):
        try:
            # Send an anonymous query to your public GitHub repo metadata
            response = requests.get(self.UPDATE_URL, timeout=5)
            
            # If no live releases exist yet on GitHub, handle the 404 cleanly
            if response.status_code == 404:
                print("No live releases found on GitHub yet. This is expected during initial setup.")
                return
                
            github_data = response.json()
            
            # Clean target tag string data (e.g., "v1.1.0" -> "1.1.0")
            latest_version = github_data["tag_name"].replace("v", "") 
            
            # Trigger update sequence if online version does not equal local current version
            if latest_version != self.CURRENT_VERSION:
                # Ensure an actual executable installation asset is linked in the release payload
                if github_data["assets"]:
                    self.after(0, lambda: self.show_update_popup(latest_version, github_data))
        except Exception as e:
            print(f"Update verification sequence failed: {e}")

    # --- POPUP UPDATE OVERLAY PANEL ---
    def show_update_popup(self, new_version, github_data):
        popup = ctk.CTkToplevel(self)
        popup.title("Update Available!")
        popup.geometry("380x200")
        popup.resizable(False, False)
        popup.attributes("-topmost", True) # Keep window prioritized on top layer

        # Informational prompt display
        msg_label = ctk.CTkLabel(
            popup, 
            text=f"A new version is available on GitHub!\n\nCurrent version: v{self.CURRENT_VERSION}\nLatest version: v{new_version}",
            font=("Arial", 13, "bold")
        )
        msg_label.pack(pady=25)

        # Control Action Buttons Container
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        # Extract primary download link payload from first index array
        download_url = github_data["assets"][0]["browser_download_url"]

        # Action: Confirmation Download Trigger
        btn_update = ctk.CTkButton(
            btn_frame, text="Download Now 🚀", fg_color="#1e90ff", font=("Arial", 12, "bold"),
            command=lambda: self.trigger_actual_download(popup, download_url)
        )
        btn_update.pack(side="left", expand=True, padx=5)

        # Action: Defer Update Dismissal
        btn_later = ctk.CTkButton(
            btn_frame, text="Later", fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"),
            command=popup.destroy
        )
        btn_later.pack(side="right", expand=True, padx=5)

    def trigger_actual_download(self, popup_window, download_url):
        popup_window.destroy()
        self.tip_label.configure(text="Downloading new deployment asset from GitHub... ⏳", text_color="#1e90ff")
        threading.Thread(target=self.download_installer_worker, args=(download_url,), daemon=True).start()

    def download_installer_worker(self, url):
        try:
            import os
            import subprocess
            
            # Determine correct localized destination filename string
            filename = url.split("/")[-1]
            download_path = os.path.join(os.environ['TEMP'], filename)
            
            # Stream payload chunk buffers directly into local AppData local temp directory
            r = requests.get(url, stream=True)
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.tip_label.configure(text="Download complete! Initializing setup installation process...", text_color="#2ed573")
            
            # Execute downloaded deployment binary setup stream
            subprocess.Popen([download_path], shell=True)
            self.quit()
            
        except Exception as e:
            self.tip_label.configure(text=f"Download transaction routine failed: {e}", text_color="#ff4757")

    # --- STANDARD UX CONTEXT LOGIC ---
    def select_mode(self, mode):
        if self.is_running: return
        self.selected_mode = mode
        default_bg, default_text = ("#ced6e0", "#2f3542"), ("#2f3542", "#f1f2f6")
        self.btn_sleep.configure(fg_color=default_bg, text_color=default_text)
        self.btn_click.configure(fg_color=default_bg, text_color=default_text)
        self.btn_teams.configure(fg_color=default_bg, text_color=default_text)
        self.btn_macro.configure(fg_color=default_bg, text_color=default_text)

        if mode == "sleep":
            self.btn_sleep.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Anti-Sleep Mode selected. Press F7 to START.")
        elif mode == "click":
            self.btn_click.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Game Autoclicker selected. Press F7 to START.")
        elif mode == "teams":
            self.btn_teams.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Smart Teams Mode selected. Press F7 to START.")
        elif mode == "macro":
            self.btn_macro.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Macro Recorder selected. View configuration settings via ⚙️.")

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

    def open_settings(self):
        print("Settings cog interaction detected!")

if __name__ == "__main__":
    app = SuperClickerGUI()
    app.mainloop()
