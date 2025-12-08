import asyncio
import json
import logging
from asyncio import CancelledError
from collections.abc import Generator
from typing import Any, AsyncGenerator, Dict, List

import aiohttp

from pyobservability.config import settings

LOGGER = logging.getLogger("uvicorn.default")
OBS_PATH = "/observability"


def refine_service(service_list: List[Dict[str, Any]]) -> Generator[Dict[str, Dict[str, str]]]:
    """Refine service stats to only include relevant fields and round CPU values.

    Args:
        service_list: List of service statistics dictionaries.

    Yields:
        Dict[str, Dict[str, str]]:
        Refined service statistics dictionary.
    """
    for service in service_list:
        service["memory"] = dict(rss=service.get("memory", {}).get("rss"), vms=service.get("memory", {}).get("vms"))
        service["cpu"] = dict(
            user=round(service.get("cpu", {}).get("user", 0), 2),
            system=round(service.get("cpu", {}).get("system", 0), 2),
        )
        yield service


class Monitor:
    """Monitor class to stream observability data from a target.

    >>> Monitor

    """

    def __init__(self, target: Dict[str, str]):
        """Initialize Monitor with target configuration.

        Args:
            target: Dictionary containing target configuration with keys 'name', 'base_url', and 'apikey'.
        """
        self.name = target["name"]
        self.base_url = target["base_url"]
        self.apikey = target["apikey"]
        self.flags = {"all_services": False}

        self.session: aiohttp.ClientSession | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

        self._ws_subscribers = []  # list of asyncio.Queue

    # ------------------------------
    # SUBSCRIBE / UNSUBSCRIBE
    # ------------------------------
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to the monitor's data stream.

        Returns:
            asyncio.Queue:
            Queue to receive streamed data.
        """
        q = asyncio.Queue(maxsize=10)
        self._ws_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """Unsubscribe from the monitor's data stream.

        Args:
            q: Queue to be removed from subscribers.
        """
        if q in self._ws_subscribers:
            self._ws_subscribers.remove(q)

    # ------------------------------
    # START / STOP
    # ------------------------------
    async def start(self):
        """Start the monitor's data streaming."""
        if self._task:
            return  # already running

        self._stop.clear()
        self.session = aiohttp.ClientSession()

        self._task = asyncio.create_task(self._stream_target())

    async def stop(self):
        """Stop the monitor's data streaming."""
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

    async def update_flags(self, **kwargs) -> None:
        """Update monitor flags and restart the stream."""
        for k, v in kwargs.items():
            if k in self.flags:
                self.flags[k] = v

        # restart stream with new params
        await self._restart_stream()

    async def _restart_stream(self) -> None:
        """Restart the monitor's data streaming."""
        await self.stop()
        await self.start()

    # ------------------------------
    # FETCH STREAM
    # ------------------------------
    async def _fetch_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch the observability data stream from the target.

        Yields:
            Dict[str, Any]:
            Parsed observability data.
        """
        query = f"?interval={settings.env.interval}"
        if self.flags["all_services"]:
            query += "&all_services=true"
        url = self.base_url.rstrip("/") + OBS_PATH + query
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
                    parsed = json.loads(line)
                    try:
                        if service_stats := parsed.get("service_stats"):
                            parsed["service_stats"] = list(refine_service(service_stats))
                    except Exception as error:
                        LOGGER.error("Received [%s: %s] when parsing services for %s", type(error), error, self.name)
                    yield parsed
                except json.JSONDecodeError:
                    LOGGER.debug("Bad JSON from %s: %s", self.base_url, line)

    # ------------------------------
    # STREAM LOOP
    # ------------------------------
    async def _stream_target(self) -> None:
        """Stream observability data from the target and notify subscribers."""
        errors = {}
        while not self._stop.is_set():
            try:
                async for payload in self._fetch_stream():
                    result = {
                        "type": "metrics",
                        "ts": asyncio.get_event_loop().time(),
                        "data": [
                            {
                                "name": self.name,
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
                if errors.get(self.base_url):
                    if errors[self.base_url] < 10:
                        LOGGER.debug("Stream error for %s: %s", self.base_url, err)
                        errors[self.base_url] += 1
                    else:
                        LOGGER.error("Stream error for %s: %s", self.base_url, err)

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
                                q.put_nowait(error_msg)
                        await self.stop()
                        return
                else:
                    errors[self.base_url] = 1

            await asyncio.sleep(1)
