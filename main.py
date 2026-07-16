import sys
import json
import threading


def run_ghost_worker():
    from modes.sleep import AntiSleepWorker

    worker_config = json.loads(sys.argv[2])
    worker = AntiSleepWorker(**worker_config)
    worker.start()

    try:
        import time
        while worker.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--ghost-worker":
        run_ghost_worker()
        sys.exit(0)

    from gui import MousieApp

    app = MousieApp()
    threading.Thread(target=app.updater.run_update_check, daemon=True).start()
    app.mainloop()
