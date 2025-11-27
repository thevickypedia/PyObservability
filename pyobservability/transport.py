import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from pyobservability.config import settings
from pyobservability.monitor import Monitor

LOGGER = logging.getLogger("uvicorn.default")


async def _forward_metrics(websocket: WebSocket, q: asyncio.Queue):
    while True:
        payload = await q.get()
        await websocket.send_json(payload)


async def websocket_endpoint(websocket: WebSocket):
    # TODO:
    #   UI - fix missing spinner
    #   Tables don't reset when node is switched
    #   Remove processes or add them through PyNinja
    await websocket.accept()

    monitor: Monitor | None = None
    q: asyncio.Queue | None = None

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # -------------------------------------------
            # UI requests a specific target to monitor
            # -------------------------------------------
            if data.get("type") == "select_target":
                base_url = data["base_url"]

                # stop old monitor
                if monitor:
                    monitor.unsubscribe(q)
                    await monitor.stop()

                for t in settings.env.targets:
                    if t["base_url"] == base_url:
                        target = t
                        break
                else:
                    LOGGER.warning(f"Invalid base url: {base_url}")
                    raise WebSocketDisconnect(code=400, reason=f"Invalid base url: {base_url}")
                LOGGER.info("Gathering metrics for: %s", target["name"])

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
