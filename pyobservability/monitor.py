import asyncio
import json
import logging
from asyncio import CancelledError
from typing import Dict

import aiohttp

from pyobservability.config import settings

LOGGER = logging.getLogger("uvicorn.default")
OBS_PATH = "/observability"


class Monitor:
    def __init__(self, target: Dict[str, str]):
        self.name = target["name"]
        self.base_url = target["base_url"]
        self.apikey = target["apikey"]

        self.session: aiohttp.ClientSession | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

        self._ws_subscribers = []  # list of asyncio.Queue

    # ------------------------------
    # SUBSCRIBE / UNSUBSCRIBE
    # ------------------------------
    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=10)
        self._ws_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._ws_subscribers:
            self._ws_subscribers.remove(q)

    # ------------------------------
    # START / STOP
    # ------------------------------
    async def start(self):
        if self._task:
            return  # already running

        self._stop.clear()
        self.session = aiohttp.ClientSession()

        self._task = asyncio.create_task(self._stream_target())

    async def stop(self):
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except CancelledError:
                pass
            self._task = None

        if self.session:
            await self.session.close()
            self.session = None

    # ------------------------------
    # FETCH STREAM
    # ------------------------------
    async def _fetch_stream(self):
        url = self.base_url.rstrip("/") + OBS_PATH + f"?interval={settings.env.interval}"
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.apikey}"}

        async with self.session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=None, connect=3, sock_read=None, sock_connect=3)
        ) as resp:
            if resp.status != 200:
                LOGGER.error("Bad response [%d] from %s", resp.status, url)
                return

            async for raw in resp.content:
                line = raw.decode().strip()
                if not line:
                    continue

                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    LOGGER.debug("Bad JSON from %s: %s", self.base_url, line)

    # ------------------------------
    # STREAM LOOP
    # ------------------------------
    async def _stream_target(self):
        errors = {}
        while not self._stop.is_set():
            try:
                async for payload in self._fetch_stream():
                    result = {
                        "type": "metrics",
                        "ts": asyncio.get_event_loop().time(),
                        "data": [
                            {
                                "name": self.base_url,
                                "base_url": self.base_url,
                                "metrics": payload,
                            }
                        ],
                    }

                    for q in list(self._ws_subscribers):
                        try:
                            q.put_nowait(result)
                        except asyncio.QueueFull:
                            _ = q.get_nowait()
                            q.put_nowait(result)
            except Exception as err:
                LOGGER.debug("Stream error for %s: %s", self.base_url, err)
                if errors.get(self.base_url):
                    if errors[self.base_url] < 10:
                        errors[self.base_url] += 1
                    else:
                        LOGGER.error("%s exceeded error threshold.", self.base_url)

                        # notify subscribers before stopping
                        error_msg = {
                            "type": "error",
                            "base_url": self.base_url,
                            "message": f"{self.name!r} is unreachable.",
                        }

                        for q in list(self._ws_subscribers):
                            try:
                                q.put_nowait(error_msg)
                            except asyncio.QueueFull as warn:
                                LOGGER.warning(warn)
                                _ = q.get_nowait()
                                q.put_nowait(result)
                        await self.stop()
                        return
                else:
                    errors[self.base_url] = 1

            await asyncio.sleep(1)
