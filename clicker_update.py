import customtkinter as ctk
import requests
import threading

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

class SuperClickerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Lokale versie van de app
        self.CURRENT_VERSION = "1.0.0"
        # URL naar het online JSON-bestand (voor de test gebruiken we een placeholder)
        self.UPDATE_URL = "https://raw.githubusercontent.com/asweigart/pyautogui/master/README.md" # Dummy URL voor netwerktest

        # Venster-instellingen
        self.title("SUPER CLICKER PRO v2.1")
        self.geometry("500x550")
        self.resizable(False, False)

        self.selected_mode = None
        self.is_running = False

        # --- SETUP INTERFACE ---
        self.setup_ui()

        # --- AUTO-UPDATE CONTROLE ---
        # We voeren dit uit in een aparte thread zodat de GUI niet haperig opstart tijdens het laden
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def setup_ui(self):
        # Tandwiel rechtsboven
        self.settings_button = ctk.CTkButton(self, text="⚙️", width=35, height=35, font=("Arial", 16), fg_color="transparent", command=self.open_settings)
        self.settings_button.place(x=450, y=10)

        # Titel
        self.title_label = ctk.CTkLabel(self, text="MODUS SELECTIE", font=("Arial", 16, "bold"), text_color=("#1e90ff", "#70a1ff"))
        self.title_label.pack(pady=(20, 15))

        # Modus kaarten frame
        self.mode_frame = ctk.CTkFrame(self, corner_radius=12)
        self.mode_frame.pack(pady=10, padx=30, fill="both", expand=True)

        self.btn_sleep = ctk.CTkButton(self.mode_frame, text="🧠  Anti-Slaapstand", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("sleep"))
        self.btn_sleep.pack(pady=8, padx=20, fill="x")

        self.btn_click = ctk.CTkButton(self.mode_frame, text="🎮  Game Autoclicker", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("click"))
        self.btn_click.pack(pady=8, padx=20, fill="x")

        self.btn_teams = ctk.CTkButton(self.mode_frame, text="🤝  Slimme Teams Modus", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("teams"))
        self.btn_teams.pack(pady=8, padx=20, fill="x")

        self.btn_macro = ctk.CTkButton(self.mode_frame, text="🎥  Macro Modus (Record/Play)", height=45, fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"), font=("Arial", 13, "bold"), command=lambda: self.select_mode("macro"))
        self.btn_macro.pack(pady=8, padx=20, fill="x")

        # Status / Help label
        self.tip_label = ctk.CTkLabel(self, text="Selecteer eerst een modus hieronder om te starten.", font=("Arial", 12, "italic"), text_color="gray")
        self.tip_label.pack(pady=10)

        # Controle acties
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=(10, 25), padx=30, fill="x")

        self.btn_start = ctk.CTkButton(self.control_frame, text="▶  START", height=50, fg_color=("#2ed573", "#26af5f"), font=("Arial", 14, "bold"), state="disabled", command=self.start_action)
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(self.control_frame, text="■  STOP", height=50, fg_color=("#ff4757", "#ff6b81"), font=("Arial", 14, "bold"), state="disabled", command=self.stop_action)
        self.btn_stop.pack(side="right", padx=5, expand=True, fill="x")

    # --- NIEUW: UPDATE CONTROLE LOGICA ---
    def check_for_updates(self):
        try:
            # In een echte situatie haal je hier een JSON op, bijv:
            # response = requests.get(self.UPDATE_URL, timeout=5).json()
            # latest_version = response["version"]
            
            # Simulatie: we doen alsof we verbinding maken en er een v1.2.0 klaarstaat
            import time
            time.sleep(2) # Korte vertraging zodat de app al open staat
            
            latest_version = "1.2.0" # Gevonden op internet
            
            if latest_version != self.CURRENT_VERSION:
                # Er is een update! Roep de popup aan in de hoofdthread van de GUI
                self.after(0, lambda: self.show_update_popup(latest_version))
        except Exception as e:
            print(f"Update check mislukt: {e}")

    # --- NIEUW: ROUVY-STYLE POPUP MELDING ---
    def show_update_popup(self, new_version):
        # Maak een nieuw venster (Toplevel) bovenop de hoofd-GUI
        popup = ctk.CTkToplevel(self)
        popup.title("Update beschikbaar!")
        popup.geometry("380x200")
        popup.resizable(False, False)
        popup.attributes("-topmost", True) # Zorg dat hij écht overal bovenop springt

        # Tekst in de popup
        msg_label = ctk.CTkLabel(
            popup, 
            text=f"Er is een nieuwe versie beschikbaar!\n\nHuidige versie: v{self.CURRENT_VERSION}\nNieuwste versie: v{new_version}",
            font=("Arial", 13, "bold")
        )
        msg_label.pack(pady=25)

        # Knoppen Frame
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        # Update Nu Knop
        btn_update = ctk.CTkButton(
            btn_frame, text="Nu Updaten 🚀", fg_color="#1e90ff", font=("Arial", 12, "bold"),
            command=lambda: self.trigger_actual_update(popup)
        )
        btn_update.pack(side="left", expand=True, padx=5)

        # Later Knop
        btn_later = ctk.CTkButton(
            btn_frame, text="Later", fg_color=("#ced6e0", "#2f3542"), text_color=("#2f3542", "#f1f2f6"),
            command=popup.destroy
        )
        btn_later.pack(side="right", expand=True, padx=5)

    def trigger_actual_update(self, popup_window):
        popup_window.destroy()
        self.tip_label.configure(text="Update wordt op de achtergrond gedownload... ⏳", text_color="#1e90ff")
        # Hier koppelen we straks het downloaden van de Setup.exe/MSI aan!

    # --- STANDAARD UX LOGICA ---
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
            self.tip_label.configure(text="Anti-Slaap geselecteerd. START met F7.")
        elif mode == "click":
            self.btn_click.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Autoclicker geselecteerd. START met F7.")
        elif mode == "teams":
            self.btn_teams.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Teams Modus geselecteerd. START met F7.")
        elif mode == "macro":
            self.btn_macro.configure(fg_color="#1e90ff", text_color="white")
            self.tip_label.configure(text="Macro Recorder geselecteerd. Opties via ⚙️.")

        self.btn_start.configure(state="normal")

    def start_action(self):
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

    def stop_action(self):
        self.is_running = False
        self.btn_stop.configure(state="disabled")
        self.btn_start.configure(state="normal")
        self.select_mode(self.selected_mode)

    def open_settings(self):
        print("Tandwiel geklikt!")

if __name__ == "__main__":
    app = SuperClickerGUI()
    app.mainloop()