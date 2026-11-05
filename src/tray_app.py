"""
Project Sirens - Desktop System Tray Controller
Provides background server monitoring, rapid dashboard access, and graceful lifecycle
controls (start/stop/quit) for both the Hub API and the Kiosk vision pipeline.
Includes automatic headless/display detection fallback for CI and server container environments.
"""

import os
import sys
import time
import signal
import webbrowser
import subprocess
import threading
from typing import Optional, Dict, Any

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pystray
    PYSTRAY_AVAILABLE = True
except (ImportError, Exception):
    pystray = None
    PYSTRAY_AVAILABLE = False


def create_tray_icon_image(size: int = 64, color: str = "#2563eb") -> Any:
    """
    Dynamically generates a crisp taskbar icon representing Project Sirens (lightning bolt on rounded square).
    Avoids requiring static binary assets in version control.
    """
    if not PIL_AVAILABLE:
        return None

    img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background square
    draw.rounded_rectangle([4, 4, size - 4, size - 4], radius=12, fill=color)

    # Lightning bolt coordinates
    bolt = [
        (size * 0.55, size * 0.18),
        (size * 0.28, size * 0.52),
        (size * 0.48, size * 0.52),
        (size * 0.42, size * 0.82),
        (size * 0.72, size * 0.45),
        (size * 0.52, size * 0.45),
    ]
    draw.polygon(bolt, fill="#ffffff")
    return img


class ServerManager:
    """
    Manages child processes for the FastAPI Hub and Kiosk Edge orchestrator.
    """
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.hub_proc: Optional[subprocess.Popen] = None
        self.kiosk_proc: Optional[subprocess.Popen] = None

    def start_hub(self, host: str = "0.0.0.0", port: int = 8000) -> bool:
        if self.is_hub_running():
            return True
        cmd = [sys.executable, "-m", "uvicorn", "hub.main:app", "--host", host, "--port", str(port)]
        self.hub_proc = subprocess.Popen(cmd, cwd=self.root_dir)
        return True

    def stop_hub(self) -> bool:
        if self.hub_proc and self.hub_proc.poll() is None:
            self.hub_proc.terminate()
            try:
                self.hub_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.hub_proc.kill()
        self.hub_proc = None
        return True

    def start_kiosk(self) -> bool:
        if self.is_kiosk_running():
            return True
        cmd = [sys.executable, "src/main.py"]
        self.kiosk_proc = subprocess.Popen(cmd, cwd=self.root_dir)
        return True

    def stop_kiosk(self) -> bool:
        if self.kiosk_proc and self.kiosk_proc.poll() is None:
            self.kiosk_proc.terminate()
            try:
                self.kiosk_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.kiosk_proc.kill()
        self.kiosk_proc = None
        return True

    def is_hub_running(self) -> bool:
        return self.hub_proc is not None and self.hub_proc.poll() is None

    def is_kiosk_running(self) -> bool:
        return self.kiosk_proc is not None and self.kiosk_proc.poll() is None

    def stop_all(self):
        self.stop_kiosk()
        self.stop_hub()


def run_tray_controller(headless: bool = False):
    """
    Initializes and starts the system tray icon loop, or headless status server if DISPLAY is missing.
    """
    manager = ServerManager()

    # Determine display environment
    has_display = bool(os.getenv("DISPLAY")) or (sys.platform in ("win32", "darwin"))
    if not PYSTRAY_AVAILABLE or headless or not has_display:
        print("[SystemTray] Operating in headless CLI monitoring mode (no graphical display detected).")
        return manager

    icon_img = create_tray_icon_image()

    def on_open_dashboard(icon, item):
        webbrowser.open("http://localhost:8000")

    def on_toggle_hub(icon, item):
        if manager.is_hub_running():
            manager.stop_hub()
        else:
            manager.start_hub()

    def on_toggle_kiosk(icon, item):
        if manager.is_kiosk_running():
            manager.stop_kiosk()
        else:
            manager.start_kiosk()

    def on_quit(icon, item):
        print("[SystemTray] Shutting down all servers and exiting...")
        manager.stop_all()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("⚡ Project Sirens Hub (Open Dashboard)", on_open_dashboard, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda text: "Stop Hub Server" if manager.is_hub_running() else "Start Hub Server", on_toggle_hub),
        pystray.MenuItem(lambda text: "Stop Kiosk Vision" if manager.is_kiosk_running() else "Start Kiosk Vision", on_toggle_kiosk),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit All & Exit", on_quit),
    )

    icon = pystray.Icon("ProjectSirens", icon_img, "Project Sirens - Retail AI", menu)
    return icon, manager


if __name__ == "__main__":
    res = run_tray_controller()
    if isinstance(res, tuple):
        icon, manager = res
        icon.run()
    else:
        # Headless loop
        print("[SystemTray] Headless controller active. Press Ctrl+C to terminate.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            res.stop_all()
            print("\n[SystemTray] Terminated.")
