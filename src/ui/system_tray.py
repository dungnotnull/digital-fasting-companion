"""
System tray application for digital-fasting-companion.

Runs the monitoring daemon in the background with a system tray icon
showing current usage status (active, warning, locked).
"""

import logging
import sys
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Try pystray, fall back gracefully
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    logger.warning("pystray + Pillow not available — system tray disabled")


class SystemTrayApp:
    """
    System tray icon for the digital fasting companion.

    Shows usage status via icon color:
    - Green: normal usage
    - Yellow: approaching threshold
    - Red: locked / intervention active
    """

    def __init__(self, on_quit=None, on_show_dashboard=None):
        self._icon: Optional["pystray.Icon"] = None
        self._status = "active"
        self._running = False
        self._on_quit = on_quit
        self._on_show_dashboard = on_show_dashboard

    def _create_image(self, color: str) -> "Image.Image":
        width, height = 64, 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        colors = {
            "active": (35, 134, 54, 255),       # green
            "warning": (210, 153, 34, 255),      # yellow
            "locked": (218, 54, 51, 255),        # red
        }
        fill = colors.get(color, colors["active"])

        draw.ellipse([8, 8, 56, 56], fill=fill, outline=(200, 200, 200, 255), width=2)
        # "DF" text
        draw.text((16, 20), "DF", fill=(255, 255, 255, 255))
        return image

    def _on_show(self, icon, item):
        if self._on_show_dashboard:
            self._on_show_dashboard()

    def _on_quit(self, icon, item):
        self._running = False
        if icon:
            icon.stop()
        if self._on_quit:
            self._on_quit()

    def update_status(self, status: str) -> None:
        """Update icon color: 'active', 'warning', 'locked'."""
        self._status = status
        if self._icon and PYSTRAY_AVAILABLE:
            self._icon.icon = self._create_image(status)

    def get_menu(self):
        menu = (
            pystray.MenuItem("Show Dashboard", self._on_show, default=True),
            pystray.MenuItem("Quit Digital Fasting", self._on_quit),
        )
        return menu

    def start(self):
        if not PYSTRAY_AVAILABLE:
            logger.info("System tray not available (install pystray + Pillow)")
            return

        self._running = True
        image = self._create_image("active")

        menu = pystray.Menu(
            pystray.MenuItem("Show Dashboard", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Digital Fasting", self._on_quit),
        )

        self._icon = pystray.Icon(
            "digital_fasting",
            image,
            "Digital Fasting Companion",
            menu,
        )

        def run_icon():
            self._icon.run()

        thread = threading.Thread(target=run_icon, daemon=True)
        thread.start()
        logger.info("System tray icon started")

    def stop(self):
        self._running = False
        if self._icon:
            self._icon.stop()
            self._icon = None
