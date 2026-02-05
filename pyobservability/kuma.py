import logging
import time
from collections import defaultdict
from urllib.parse import urlparse

import socketio

from pyobservability.config import settings

LOGGER = logging.getLogger("uvicorn.default")


async def get_kuma_data(timeout=5):
    sio = socketio.Client()
    monitors = {}

    @sio.on("monitorList")
    def on_monitor_list(data):
        LOGGER.info("Received monitor list: %d", len(data))
        nonlocal monitors
        monitors = data

    def login():
        result = {"ok": False}

        def cb(resp):
            # TODO:
            #   1. Re-use token from response payload upon successful login
            #   2. Cache the result
            #   3. Remove the logging
            #   4. Objectify this
            LOGGER.info("Response received from kuma server: %s", resp)
            nonlocal result
            result = resp or {"ok": False}

        sio.emit(
            "login",
            {"username": settings.env.kuma_username, "password": settings.env.kuma_password, "token": ""},
            callback=cb,
        )

        end_auth = time.time()
        while not result.get("ok") and time.time() < (end_auth + timeout):
            time.sleep(0.05)

        if not result.get("ok"):
            LOGGER.error("Failed to login to kuma endpoint.")
            raise RuntimeError("Uptime Kuma login failed")

    LOGGER.info("Connecting to the kuma endpoint")
    sio.connect(settings.env.kuma_url)
    login()

    end_retrieve = time.time()
    while not monitors and time.time() < (end_retrieve + timeout):
        time.sleep(0.05)

    sio.disconnect()

    if not monitors:
        LOGGER.error("No monitors were received.")
        raise RuntimeError("No monitors received")

    return monitors


async def extract_monitors(payload: dict) -> list[dict]:
    """
    Convert raw API payload into a list of dicts with:
    name, url, tag_names, host
    """
    monitors = []

    grouped = {}
    for monitor in payload.values():
        if children_ids := monitor.get("childrenIDs"):
            for child in children_ids:
                grouped[child] = monitor.get("name")

    for monitor in payload.values():
        url = monitor.get("url").replace("host.docker.internal", urlparse(settings.env.kuma_url).hostname)
        host = urlparse(url).hostname if url else None
        if not host: continue
        monitors.append({
            "name": monitor.get("name"),
            "parent": grouped.get(monitor.get("id")),
            "url": url,
            "host": host,
            "tag_names": [
                tag.get("name") for tag in monitor.get("tags", []) if "name" in tag
            ],
        })
    return monitors


async def group_by_host(monitors: list[dict]) -> dict:
    grouped = defaultdict(list)

    for monitor in monitors:
        grouped[monitor["host"]].append(monitor)

    return dict(grouped)
