import asyncio
import json
import logging
import pathlib
import warnings

import uiauth
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute, APIWebSocketRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pyobservability.config import enums, settings
from pyobservability.monitor import Monitor

LOGGER = logging.getLogger("uvicorn.default")

PyObservability = FastAPI(title="PyObservability")
PyObservability.__name__ = "PyObservability"
PyObservability.description = "Observability page for nodes running PyNinja"

root = pathlib.Path(__file__).parent
templates_dir = root / "templates"
templates = Jinja2Templates(directory=templates_dir)

static_dir = root / "static"
PyObservability.mount("/static", StaticFiles(directory=static_dir), name="static")


async def index(request: Request):
    """Pass configured targets to the template so frontend can prebuild UI.

    Args:
        request: FastAPI request object.
    """
    return templates.TemplateResponse("index.html", {"request": request, "targets": settings.env.targets})


async def _forward_metrics(websocket: WebSocket, q: asyncio.Queue):
    while True:
        payload = await q.get()
        await websocket.send_json(payload)


async def websocket_endpoint(websocket: WebSocket):
    # TODO:
    #   monitor.py - if host is unreachable (log it) for more than 3 times show error in UI
    #   UI - show spinner on each box until data is received
    #   All tables should have pages with a dedicated max items per page
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

                target = None
                for t in settings.env.targets:
                    if t["base_url"] == base_url:
                        target = t

                # create new monitor
                monitor = Monitor(base_url=base_url, apikey=target["apikey"], poll_interval=settings.env.interval)
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


def include_routes():
    if all((settings.env.username, settings.env.password)):
        uiauth.protect(
            app=PyObservability,
            username=settings.env.username,
            password=settings.env.password,
            params=[
                uiauth.Parameters(
                    path=enums.APIEndpoints.root,
                    function=index,
                    methods=["GET"],
                ),
                uiauth.Parameters(
                    path=enums.APIEndpoints.ws,
                    function=websocket_endpoint,
                    route=APIWebSocketRoute,
                ),
            ],
        )
    else:
        warnings.warn("\n\tRunning PyObservability without any protection.", UserWarning)
        PyObservability.routes.append(
            APIRoute(
                path=enums.APIEndpoints.root,
                endpoint=index,
                methods=["GET"],
                include_in_schema=False,
            ),
        )
        PyObservability.routes.append(
            APIWebSocketRoute(
                path=enums.APIEndpoints.ws,
                endpoint=websocket_endpoint,
            )
        )


def start(**kwargs):
    settings.env = settings.env_loader(**kwargs)
    settings.env.targets = [{k: str(v) for k, v in target.model_dump().items()} for target in settings.env.targets]
    include_routes()
    uvicorn_args = dict(
        host=settings.env.host,
        port=settings.env.port,
        app=PyObservability,
    )
    uvicorn.run(**uvicorn_args)
