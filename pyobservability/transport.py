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


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint to handle observability data streaming.

    Args:
        websocket: FastAPI WebSocket connection.
    """
    await websocket.accept()

    monitor: Monitor | None = None
    q: asyncio.Queue | None = None

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            if data.get("type") == "update_flags":
                if monitor:
                    await monitor.update_flags(
                        all_services=data.get("all_services", False),
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
