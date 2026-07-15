import os
import requests
import subprocess
import threading


class MousieUpdater:
    def __init__(self, app_instance):
        # Keep a reference to the main GUI to update labels/status
        self.app = app_instance
        self.UPDATE_URL = "https://api.github.com/repos/hyreduki/mousie/releases/latest"

    def run_update_check(self):
        try:
            response = requests.get(self.UPDATE_URL, timeout=5)
            if response.status_code == 404:
                print("No live releases found on GitHub yet.")
                return

            github_data = response.json()
            latest_version = github_data["tag_name"].lower().replace("v", "")

            if latest_version != self.app.CURRENT_VERSION:
                if github_data["assets"]:
                    # Safely communicate back to the main GUI thread
                    self.app.after(0, lambda: self.app.show_update_popup(latest_version, github_data))
        except Exception as e:
            print(f"Update verification routine failed: {e}")

    def _set_tip_label(self, text, text_color):
        self.app.after(0, lambda: self.app.tip_label.configure(text=text, text_color=text_color))

    def start_download_worker(self, download_url):
        self._set_tip_label("Downloading new deployment asset from GitHub... ⏳", "#1e90ff")
        threading.Thread(target=self._download_executor, args=(download_url,), daemon=True).start()

    def _download_executor(self, url):
        try:
            filename = url.split("/")[-1]
            download_path = os.path.join(os.environ['TEMP'], filename)

            response = requests.get(url, stream=True)
            with open(download_path, 'wb') as file_stream:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_stream.write(chunk)

            self._set_tip_label("Download complete! Initializing setup process...", "#2ed573")
            self.app.after(0, lambda: [subprocess.Popen([download_path], shell=True), self.app.quit()])
        except Exception as e:
            self._set_tip_label(f"Download transaction routine failed: {e}", "#ff4757")