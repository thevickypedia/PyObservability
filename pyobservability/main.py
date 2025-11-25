import logging
import pathlib

import dotenv
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute, APIWebSocketRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pyobservability.config import env
from pyobservability.monitor import Monitor

dotenv.load_dotenv()

LOGGER = logging.getLogger("uvicorn.default")

PyObservability = FastAPI(title="PyObservability")
PyObservability.__name__ = "PyObservability"
PyObservability.description = "Observability page for nodes running PyNinja"

root = pathlib.Path(__file__).parent
templates_dir = root / "templates"
templates = Jinja2Templates(directory=templates_dir)

static_dir = root / "static"
PyObservability.mount("/static", StaticFiles(directory=static_dir), name="static")

monitor = Monitor(targets=env.monitor_targets, poll_interval=env.poll_interval)


async def index(request: Request):
    """Pass configured targets to the template so frontend can prebuild UI.

    Args:
        request: FastAPI request object.
    """
    return templates.TemplateResponse("index.html", {"request": request, "targets": monitor.targets})


async def websocket_endpoint(websocket: WebSocket):
    """Websocket endpoint to render the metrics.

    Args:
        websocket: FastAPI websocket object.
    """
    await websocket.accept()
    await monitor.start()
    q = monitor.subscribe()
    try:
        while True:
            payload = await q.get()
            # send as JSON text
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        monitor.unsubscribe(q)
    except Exception:
        monitor.unsubscribe(q)
        try:
            await websocket.close()
        except Exception as err:
            LOGGER.warning(err)
            pass
    await monitor.stop()


PyObservability.routes.append(
    APIRoute(
        path="/",  # enums.APIEndpoints.root,
        endpoint=index,
        methods=["GET"],
        include_in_schema=False,
    ),
)
PyObservability.routes.append(
    APIWebSocketRoute(
        path="/ws",
        endpoint=websocket_endpoint,
    )
)


def start():
    uvicorn_args = dict(
        host=env.host,
        port=env.port,
        app=PyObservability,
    )
    uvicorn.run(**uvicorn_args)
