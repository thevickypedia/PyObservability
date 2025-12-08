import asyncio
import json
import logging

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


def _normalize_targets() -> list[dict]:
    """Return configuration targets sorted so legend colors are consistent."""
    return sorted(settings.env.targets, key=lambda t: t["name"].lower())


async def _forward_metrics_multi(
    websocket: WebSocket,
    queues: list[asyncio.Queue],
    monitors: list[Monitor],
    targets: list[dict],
) -> None:
    """Fan-in metrics from multiple monitors and emit once every node updates."""
    latest: dict[str, dict] = {}
    try:
        while True:
            for idx, q in enumerate(queues):
                payload = await q.get()
                latest[targets[idx]["base_url"]] = payload

            if len(latest) != len(targets):
                continue

            merged = {
                "type": "metrics",
                "ts": asyncio.get_event_loop().time(),
                "data": [],
            }
            for target in targets:
                sample = latest.get(target["base_url"])
                if not sample:
                    continue
                merged["data"].extend(sample["data"])
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
    monitors: list[Monitor] = []
    queues: list[asyncio.Queue] = []
    multi_task: asyncio.Task | None = None

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

                # stop old monitor
                if monitor:
                    monitor.unsubscribe(q)
                    await monitor.stop()
                    monitor = None
                    q = None
                if multi_task:
                    multi_task.cancel()
                    multi_task = None
                for idx, mon in enumerate(monitors):
                    mon.unsubscribe(queues[idx])
                    await mon.stop()
                monitors.clear()
                queues.clear()

                if base_url == "*":
                    # TODO: If errors exceed threshold, UI freezes but the node should be skipped instead
                    targets = _normalize_targets()
                    for target in targets:
                        mon = Monitor(target)
                        await mon.start()
                        monitors.append(mon)
                        queues.append(mon.subscribe())
                    multi_task = asyncio.create_task(_forward_metrics_multi(websocket, queues, monitors, targets))
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
                asyncio.create_task(_forward_metrics(websocket, q))
    except WebSocketDisconnect:
        pass
    except Exception as err:
        LOGGER.error("WS error: %s", err)

    # cleanup
    if monitor:
        if q:
            monitor.unsubscribe(q)
        await monitor.stop()

    if multi_task:
        multi_task.cancel()

    for idx, mon in enumerate(monitors):
        mon.unsubscribe(queues[idx])
        await mon.stop()
