# app/monitor.py

import asyncio
import json
import logging
import os
from asyncio import CancelledError
from typing import Any, Dict, List
from urllib.parse import urlparse

import aiohttp

LOGGER = logging.getLogger("uvicorn.default")

###############################################################################
# ENDPOINT DEFINITIONS (PyNinja Correct)
###############################################################################

ENDPOINTS = {
    "ip": {
        "path": "/get-ip",
        "params": {"public": "false"},
    },
    "cpu": {
        "path": "/get-cpu",
        "params": {"interval": 2, "per_cpu": "true"},
    },
    "cpu_load": {
        "path": "/get-cpu-load",
        "params": {},
    },
    "gpu": {
        "path": "/get-processor",
        "params": {},
    },
    "memory": {
        "path": "/get-memory",
        "params": {},
    },
    "disk": {
        "path": "/get-disk-utilization",
        "params": {"path": "/"},
    },
    "disks": {
        "path": "/get-all-disks",
        "params": {},
    },
    "services": {
        "path": "/get-all-services",
        "params": {},
    },
    "docker_stats": {
        "path": "/get-docker-stats",
        "params": {},
    },
    "certificates": {
        "path": "/get-certificates",
        "params": {},
    },
}


###############################################################################
# LOAD TARGETS FROM ENV
###############################################################################


def load_targets_from_env() -> List[Dict[str, Any]]:
    """Loads monitor targets from environment variables and parses it.

    Returns:
        List[Dict[str, Any]]:
        Returns the parsed list of the monitor targets.
    """
    raw = os.getenv("MONITOR_TARGETS", "[]")

    try:
        data = json.loads(raw)
    except Exception:
        data = [raw] if raw else []

    parsed = []

    for entry in data:
        if isinstance(entry, str):
            parsed.append({"name": entry, "base_url": entry, "apikey": None})
        elif isinstance(entry, dict):
            parsed.append(
                {
                    "name": entry.get("name") or entry["base_url"],
                    "base_url": entry["base_url"],
                    "apikey": entry.get("apikey"),
                }
            )

    return parsed


###############################################################################
# MONITOR CLASS
###############################################################################


class Monitor:

    def __init__(self, poll_interval: float = 2.0):
        self.targets = load_targets_from_env()
        self.poll_interval = float(os.getenv("POLL_INTERVAL", poll_interval))
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self._ws_subscribers: List[asyncio.Queue] = []
        self._task = None
        self._stop = asyncio.Event()

    ############################################################################
    # LIFECYCLE
    ############################################################################
    async def start(self):
        for t in self.targets:
            self.sessions[t["base_url"]] = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._run_loop())

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
    # FETCH WRAPPER
    ############################################################################
    async def _fetch(self, session, base_url, ep, apikey=None, params=None):
        url = base_url.rstrip("/") + ep
        headers = {"accept": "application/json"}
        if apikey:
            headers["Authorization"] = f"Bearer {apikey}"

        try:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                if resp.status == 200:
                    try:
                        return await resp.json()
                    except Exception as err:
                        LOGGER.debug(err)
                        return "NO DATA"
                parsed = urlparse(url)
                LOGGER.debug("Exception on '%s' - [%d]: %s", parsed.path, resp.status, await resp.text())
                return "NO DATA"
        except Exception as err:
            LOGGER.debug(err)
            return "NO DATA"

    ############################################################################
    # PER-TARGET POLLING
    ############################################################################
    async def _poll_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        base = target["base_url"]
        apikey = target.get("apikey")
        session = self.sessions[base]

        result = {"name": target["name"], "base_url": base, "metrics": {}}

        # Fire ALL requests concurrently
        tasks = {}

        for key, cfg in ENDPOINTS.items():
            tasks[key] = asyncio.create_task(
                self._fetch(session, base, cfg["path"], apikey=apikey, params=cfg["params"])
            )

        # Wait for all endpoints
        raw_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for (key, _), resp in zip(tasks.items(), raw_results):
            if isinstance(resp, Exception):
                result["metrics"][key] = "NO DATA"
                continue
            if isinstance(resp, dict):
                result["metrics"][key] = resp.get("detail", resp)
            else:
                # raw string / number / list / etc
                result["metrics"][key] = resp

        return result

    ############################################################################
    # POLL ALL HOSTS
    ############################################################################
    async def _poll_all(self) -> List[Dict[str, Any]]:
        tasks = [self._poll_target(t) for t in self.targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out = []
        for r in results:
            if isinstance(r, Exception):
                LOGGER.error("%s", r)
                out.append({"error": str(r)})
            else:
                out.append(r)
        return out

    ############################################################################
    # MAIN LOOP
    ############################################################################
    async def _run_loop(self):
        while not self._stop.is_set():
            metrics = await self._poll_all()

            payload = {"type": "metrics", "ts": asyncio.get_event_loop().time(), "data": metrics}

            for q in list(self._ws_subscribers):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    try:
                        _ = q.get_nowait()
                        q.put_nowait(payload)
                    except Exception:
                        pass

            await asyncio.sleep(self.poll_interval)
