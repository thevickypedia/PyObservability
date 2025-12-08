import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect

from pyobservability.config import settings
from pyobservability.monitor import Monitor

LOGGER = logging.getLogger("uvicorn.default")


async def _forward_metrics(websocket: WebSocket, q: asyncio.Queue) -> None:
    """Forward metrics from the monitor's queue to the websocket.

    Args:
        websocket: FastAPI WebSocket connection.
        q: asyncio.Queue to receive metrics from the monitor.
    """
    while True:
        payload = await q.get()
        await websocket.send_json(payload)


def _normalize_targets() -> List[Dict[str, str]]:
    """Return configuration targets sorted so legend colors are consistent."""
    return sorted(settings.env.targets, key=lambda t: t["name"].lower())


async def _forward_metrics_multi(
    websocket: WebSocket,
    queues: List[asyncio.Queue],
    targets: List[Dict[str, str]],
) -> None:
    """Fan-in metrics from multiple monitors and emit once every node updates.

    Args:
        websocket: FastAPI WebSocket connection.
        queues: List of asyncio.Queues from multiple monitors.
        targets: List of target configurations corresponding to the queues.

    Notes:
        This is resilient to individual node failures.
        If a monitor starts emitting an ``error`` payload (e.g. exceeded error threshold),
        that node is marked as failed and removed from the unified stream,
        so that the remaining nodes keep updating in the UI.
    """
    # Track active (non-failed) indices
    active = [True] * len(queues)

    # Latest payload per node keyed by base_url
    latest: Dict[str, dict] = {}
    try:
        while True:
            # If all nodes have failed, stop the unified stream loop.
            if not any(active):
                LOGGER.info("All targets in unified stream have failed; stopping multi-node forwarder")
                return

            # Wait for at least one payload from any active queue.
            # We gather one payload per active queue in a "round", but we do
            # not block forever on failed queues because we mark them inactive
            # as soon as they send an error.
            for idx, q in enumerate(queues):
                if not active[idx]:
                    continue

                payload = await q.get()

                # Handle error payloads from monitors: mark this node as failed
                # and notify the UI once, then skip it from future
                # rounds so the rest of the nodes continue streaming.
                if isinstance(payload, dict) and payload.get("type") == "error":
                    base_url = targets[idx]["base_url"]
                    LOGGER.warning("Unified stream: target %s reported error and will be skipped", base_url)

                    # Forward the error to the websocket so the UI can show it.
                    try:
                        await websocket.send_json(payload)
                    except Exception as send_err:  # pragma: no cover - defensive
                        LOGGER.debug("Failed to send error payload to WS: %s", send_err)

                    # Mark this target as inactive and remove its latest sample
                    active[idx] = False
                    latest.pop(base_url, None)
                    continue

                # Normal metrics payload: remember latest per base_url
                base_url = targets[idx]["base_url"]
                latest[base_url] = payload

            # Build merged message from all currently active targets that have
            # produced at least one metrics payload.
            merged = {
                "type": "metrics",
                "ts": asyncio.get_event_loop().time(),
                "data": [],
            }

            for idx, target in enumerate(targets):
                if not active[idx]:
                    continue
                sample = latest.get(target["base_url"])
                if not sample:
                    continue
                merged["data"].extend(sample.get("data", []))

            # If we have no data (e.g. new round before any active node
            # produced metrics), skip sending to avoid spamming empty payloads.
            if not merged["data"]:
                continue

            await websocket.send_json(merged)
    except asyncio.CancelledError:
        LOGGER.debug("Unified stream task cancelled")


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Websocket endpoint to handle observability data streaming.

    Args:
        websocket: FastAPI WebSocket connection.
    """
    await websocket.accept()

    monitor: Monitor | None = None
    q: asyncio.Queue | None = None
    monitors: List[Monitor] = []
    queues: List[asyncio.Queue] = []
    multi_task: asyncio.Task | None = None
    forward_task: asyncio.Task | None = None

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            if data.get("type") == "update_flags":
                if monitor:
                    await monitor.update_flags(
                        all_services=data.get("all_services", False),
                    )
                elif monitors:
                    await asyncio.gather(
                        *(
                            mon.update_flags(
                                all_services=data.get("all_services", False),
                            )
                            for mon in monitors
                        )
                    )
                continue

            # -------------------------------------------
            # UI requests a specific target to monitor
            # -------------------------------------------
            if data.get("type") == "select_target":
                base_url = data["base_url"]

                # stop old monitor / tasks
                if forward_task:
                    LOGGER.info("Stopping previous forwarder task")
                    forward_task.cancel()
                    forward_task = None

                if monitor:
                    LOGGER.info("Stopping previous monitor task")
                    monitor.unsubscribe(q)
                    await monitor.stop()
                    monitor = None
                    q = None

                if multi_task:
                    LOGGER.info("Stopping previous multi-target forwarder task")
                    multi_task.cancel()
                    multi_task = None

                LOGGER.info("Unsubscribing from previous monitors") if monitor else None
                for idx, mon in enumerate(monitors):
                    mon.unsubscribe(queues[idx])
                    await mon.stop()

                monitors.clear()
                queues.clear()

                if base_url == "*":
                    LOGGER.info("Gathering metrics for all targets in unified stream")
                    targets = _normalize_targets()
                    for target in targets:
                        mon = Monitor(target)
                        await mon.start()
                        monitors.append(mon)
                        queues.append(mon.subscribe())
                    multi_task = asyncio.create_task(_forward_metrics_multi(websocket, queues, targets))
                    continue

                if target := settings.targets_by_url.get(base_url):
                    LOGGER.info("Gathering metrics for: %s", target["name"])
                else:
                    LOGGER.warning(f"Invalid base url: {base_url}")
                    raise WebSocketDisconnect(code=400, reason=f"Invalid base url: {base_url}")

                # create new monitor
                monitor = Monitor(target)
                await monitor.start()

                # new subscription queue
                q = monitor.subscribe()

                # start forwarding metrics
                forward_task = asyncio.create_task(_forward_metrics(websocket, q))
    except WebSocketDisconnect:
        pass
    except Exception as err:
        LOGGER.error("WS error: %s", err)

    # cleanup
    if forward_task:
        forward_task.cancel()

    if monitor:
        if q:
            monitor.unsubscribe(q)
        await monitor.stop()

    if multi_task:
        multi_task.cancel()

    for idx, mon in enumerate(monitors):
        mon.unsubscribe(queues[idx])
        await mon.stop()
