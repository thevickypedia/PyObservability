import asyncio
import json
import logging
from asyncio import CancelledError
from typing import Dict, List

import aiohttp

LOGGER = logging.getLogger("uvicorn.default")
OBS_PATH = "/observability"


class Monitor:
    def __init__(self, targets: List[Dict[str, str]], poll_interval: float):
        self.targets = targets
        self.poll_interval = poll_interval
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self._ws_subscribers: List[asyncio.Queue] = []
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    ############################################################################
    # LIFECYCLE
    ############################################################################
    async def start(self):
        self._tasks = []

        for target in self.targets:
            base = target["base_url"]
            name = target.get("name")
            apikey = target.get("apikey")

            session = aiohttp.ClientSession()
            self.sessions[base] = session

            task = asyncio.create_task(self._stream_target(name, base, session, apikey))
            self._tasks.append(task)

    async def stop(self):
        self._stop.set()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except CancelledError:
                pass

        for session in self.sessions.values():
            await session.close()

    ############################################################################
    # SUBSCRIBE / UNSUBSCRIBE
    ############################################################################
    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=10)
        self._ws_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        try:
            self._ws_subscribers.remove(q)
        except ValueError:
            pass

    ############################################################################
    # FETCH OBSERVABILITY FOR SINGLE TARGET
    ############################################################################
    async def _fetch_observability(self, session, base_url, apikey):
        url = base_url.rstrip("/") + OBS_PATH + f"?interval={self.poll_interval}"
        headers = {"accept": "application/json"}
        if apikey:
            headers["Authorization"] = f"Bearer {apikey}"

        try:
            async with session.get(url, headers=headers, timeout=None) as resp:
                if resp.status != 200:
                    LOGGER.debug("Exception - [%d]: %s", resp.status, await resp.text())
                    return
                async for line in resp.content:
                    line = line.decode().strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                        # yield each record instead of returning
                        yield payload
                    except json.JSONDecodeError as err:
                        LOGGER.debug("JSON decode error: %s | line=%s", err, line)
        except Exception as err:
            LOGGER.debug("Exception: %s", err)
            return

    ############################################################################
    # POLL LOOP - SEQUENTIAL OVER ALL TARGETS
    ############################################################################
    async def _stream_target(self, name, base, session, apikey):
        async for payload in self._fetch_observability(session, base, apikey):
            result = {
                "type": "metrics",
                "ts": asyncio.get_event_loop().time(),
                "data": [{"name": name, "base_url": base, "metrics": payload}],
            }

            # Broadcast to subscribers
            for q in list(self._ws_subscribers):
                try:
                    q.put_nowait(result)
                except asyncio.QueueFull as debug:
                    LOGGER.debug(debug)
                    try:
                        _ = q.get_nowait()
                        q.put_nowait(result)
                    except Exception as warn:
                        LOGGER.warning(warn)
