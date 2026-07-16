import os
import sys
import json
import shutil
import subprocess

GHOST_PROCESS_OPTIONS = [
    "RuntimeBroker.exe",
    "svchost.exe",
    "dllhost.exe",
    "conhost.exe",
]

CREATE_NO_WINDOW = 0x08000000


def is_frozen():
    return getattr(sys, "frozen", False)


def get_ghost_executable_path(disguise_name):
    ghost_dir = os.path.join(os.environ["LOCALAPPDATA"], "Mousie", "ghost")
    os.makedirs(ghost_dir, exist_ok=True)
    return os.path.join(ghost_dir, disguise_name)


def prepare_ghost_executable(disguise_name):
    if not is_frozen():
        return None

    ghost_path = get_ghost_executable_path(disguise_name)
    source_mtime = os.path.getmtime(sys.executable)
    if not os.path.exists(ghost_path) or os.path.getmtime(ghost_path) < source_mtime:
        shutil.copy2(sys.executable, ghost_path)
    return ghost_path


def spawn_disguised_sleep_worker(disguise_name, worker_config):
    ghost_exe = prepare_ghost_executable(disguise_name)
    if not ghost_exe:
        return None

    return subprocess.Popen(
        [ghost_exe, "--ghost-worker", json.dumps(worker_config)],
        creationflags=CREATE_NO_WINDOW,
    )


class ProcessGhost:
    def __init__(self, app_window):
        self.app = app_window
        self.original_title = None
        self._active = False
        self.ghost_process = None

    def activate(self, disguise_name):
        if not disguise_name:
            return

        self.original_title = self.app.title()
        window_title = disguise_name.replace(".exe", "")
        self.app.title(window_title)
        self.app.attributes("-toolwindow", True)
        self.app.update_idletasks()
        self._active = True

    def deactivate(self):
        if not self._active:
            return

        if self.original_title:
            self.app.title(self.original_title)
        self.app.attributes("-toolwindow", False)
        self._active = False

    def start_disguised_worker(self, disguise_name, worker_config):
        self.ghost_process = spawn_disguised_sleep_worker(disguise_name, worker_config)
        return self.ghost_process is not None

    def stop_disguised_worker(self):
        if self.ghost_process and self.ghost_process.poll() is None:
            self.ghost_process.terminate()
            try:
                self.ghost_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.ghost_process.kill()
        self.ghost_process = None
