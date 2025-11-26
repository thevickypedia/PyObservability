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
        for target in self.targets:
            self.sessions[target["base_url"]] = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except CancelledError:
                pass

        for sess in self.sessions.values():
            await sess.close()

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
                    return None
                async for line in resp.content:
                    line = line.decode().strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                        return payload
                    except json.JSONDecodeError as err:
                        LOGGER.debug("JSON decode error: %s | line=%s", err, line)
        except Exception as err:
            LOGGER.debug("Exception: %s", err)
            return None

    ############################################################################
    # POLL LOOP - SEQUENTIAL OVER ALL TARGETS
    ############################################################################
    async def _poll_loop(self):
        while not self._stop.is_set():
            all_data = []

            # Build async tasks for all targets
            tasks = []
            meta = []  # keep name/base for each task
            for target in self.targets:
                base = target["base_url"]
                name = target.get("name")
                apikey = target.get("apikey")
                session = self.sessions.get(base)
                if session is None:
                    session = aiohttp.ClientSession()
                    self.sessions[base] = session

                tasks.append(self._fetch_observability(session, base, apikey))
                meta.append((name, base))

            # Run all fetches concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Build the aggregated result
            for (name, base), payload in zip(meta, results):
                if isinstance(payload, Exception):
                    LOGGER.debug("Exception while fetching from %s: %s", base, payload)
                    continue
                if payload:
                    all_data.append({"name": name, "base_url": base, "metrics": payload})
                else:
                    LOGGER.debug("No payload received")

            if all_data:
                result = {
                    "type": "metrics",
                    "ts": asyncio.get_event_loop().time(),
                    "data": all_data
                }

                # broadcast to all subscribers
                for q in list(self._ws_subscribers):
                    try:
                        q.put_nowait(result)
                    except asyncio.QueueFull:
                        try:
                            _ = q.get_nowait()
                            q.put_nowait(result)
                        except Exception:
                            pass
            else:
                LOGGER.debug("No data received")
