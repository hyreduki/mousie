import threading
from gui import MousieApp

if __name__ == "__main__":
    # Create the visual application instance
    app = MousieApp()

    # Start the network check loop asynchronously right after launch
    threading.Thread(target=app.updater.run_update_check, daemon=True).start()

    # Execute the core UI window frame loop
    app.mainloop()