import logging
import time
from collections.abc import Generator
from typing import Any, Dict, List
from urllib.parse import urlparse

import socketio

from pyobservability.config import settings

LOGGER = logging.getLogger("uvicorn.default")


class UptimeKumaClient:
    """Client to interact with Uptime Kuma server via Socket.IO.

    >>> UptimeKumaClient

    """

    def __init__(self):
        """Initialize the Uptime Kuma client."""
        self.sio = socketio.Client()
        self.monitors = {}
        self.logged_in = False

        self.sio.on("monitorList", self._on_monitor_list)

    def _on_monitor_list(self, data):
        """Handle incoming monitor list from Uptime Kuma server."""
        LOGGER.debug("Received monitor list from Uptime Kuma server.")
        self.monitors = data

    def connect(self):
        """Connect to the Uptime Kuma server via Socket.IO."""
        LOGGER.debug("Connecting to Uptime Kuma server at %s", settings.env.kuma_url)
        self.sio.connect(settings.env.kuma_url)

    def login(self):
        """Log in to the Uptime Kuma server."""
        result = {"ok": False}

        def callback(resp):
            """Callback to handle login response."""
            result.update(resp or {"ok": False})

        self.sio.emit(
            "login",
            {
                "username": settings.env.kuma_username,
                "password": settings.env.kuma_password,
                "token": "",
            },
            callback=callback,
        )

        end = time.time() + settings.env.kuma_timeout
        while not result.get("ok") and time.time() < end:
            time.sleep(0.05)

        if not result.get("ok"):
            raise RuntimeError("Uptime Kuma login failed")

        self.logged_in = True

    def get_monitors(self):
        """Retrieve monitors from the Uptime Kuma server."""
        if not self.sio.connected:
            self.connect()

        if not self.logged_in:
            self.login()

        end = time.time() + settings.env.kuma_timeout
        while not self.monitors and time.time() < end:
            time.sleep(0.05)

        if not self.monitors:
            raise RuntimeError("No monitors received")

        return self.monitors


def extract_monitors(payload: Dict[int, Dict[str, Any]]) -> Generator[Dict[str, Any]]:
    """Convert raw API payload into a list of dicts with name, url, tag_names, host.

    Args:
        payload: Raw payload from Uptime Kuma server.

    Yields:
        Dict[str, Any]:
        Monitors with relevant fields.
    """
    grouped = {}
    for monitor in payload.values():
        if children_ids := monitor.get("childrenIDs"):
            for child in children_ids:
                grouped[child] = monitor.get("name")

    for monitor in payload.values():
        url = monitor.get("url").replace("host.docker.internal", urlparse(settings.env.kuma_url).hostname)
        host = urlparse(url).hostname if url else None
        if not host:
            continue
        yield {
            "name": monitor.get("name"),
            "parent": grouped.get(monitor.get("id")),
            "url": url,
            "host": host,
            "tag_names": [tag.get("name") for tag in monitor.get("tags", []) if "name" in tag],
        }
