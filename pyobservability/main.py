import logging
import pathlib
import warnings
from datetime import datetime
from http import HTTPStatus
from typing import Dict

import uiauth
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute, APIWebSocketRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pyobservability.config import enums, settings
from pyobservability.kuma import UptimeKumaClient, extract_monitors
from pyobservability.transport import websocket_endpoint
from pyobservability.version import __version__

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

    Returns:
        TemplateResponse:
        Rendered HTML template with targets and version.
    """
    kuma_data = [{}] if all((settings.env.kuma_url, settings.env.kuma_username, settings.env.kuma_password)) else None
    args = dict(request=request, kuma_data=kuma_data, targets=settings.env.targets, version=__version__)
    if settings.env.username and settings.env.password:
        args["logout"] = uiauth.enums.APIEndpoints.fastapi_logout.value
    return templates.TemplateResponse("index.html", args)


async def kuma():
    """Kuma endpoint to retrieve monitors from Kuma server.

    Returns:
        List[Dict[str, Any]]:
        List of monitors from Kuma server after filtering the required fields.
    """
    try:
        kuma_data = UptimeKumaClient().get_monitors()
        LOGGER.info("Retrieved monitors from kuma server - %d found", len(kuma_data))
    except RuntimeError:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE.real,
            detail="Unable to retrieve data from kuma server.",
        )
    monitors = list(extract_monitors(kuma_data))
    LOGGER.info("Processed [%d] monitors for UI payload.", len(monitors))
    return monitors


async def health() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Dict[str, str]:
        Health status.
    """
    return {"status": "ok"}


def include_routes() -> None:
    """Include routes in the FastAPI app with or without authentication."""
    PyObservability.routes.append(
        APIRoute(
            path=enums.APIEndpoints.health,
            endpoint=health,
            methods=["GET"],
            include_in_schema=False,
        ),
    )
    kuma_enabled = all((settings.env.kuma_url, settings.env.kuma_username, settings.env.kuma_password))
    if all((settings.env.username, settings.env.password)):
        auth_endpoints = [
            uiauth.Parameters(
                path=enums.APIEndpoints.root,
                function=index,
                methods=[uiauth.enums.APIMethods.GET],
            ),
            uiauth.Parameters(
                path=enums.APIEndpoints.ws,
                function=websocket_endpoint,
                route=APIWebSocketRoute,
            ),
        ]
        if kuma_enabled:
            auth_endpoints.append(
                uiauth.Parameters(
                    path=enums.APIEndpoints.kuma,
                    function=kuma,
                    methods=[uiauth.enums.APIMethods.GET],
                )
            )
        uiauth.protect(
            app=PyObservability,
            username=settings.env.username,
            password=settings.env.password,
            timeout=settings.env.timeout,
            custom_logger=LOGGER,
            params=auth_endpoints,
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
            ),
        )
        if kuma_enabled:
            PyObservability.routes.append(
                APIRoute(
                    path=enums.APIEndpoints.kuma,
                    endpoint=kuma,
                    methods=["GET"],
                    include_in_schema=False,
                ),
            )


# noinspection PyTypeChecker
def start(**kwargs) -> None:
    """Start the FastAPI app with Uvicorn server."""
    settings.env = settings.env_loader(**kwargs)
    settings.env.targets = [{k: str(v) for k, v in target.model_dump().items()} for target in settings.env.targets]
    settings.targets_by_url = {t["base_url"]: t for t in settings.env.targets}
    include_routes()
    uvicorn_args = dict(
        host=settings.env.host,
        port=settings.env.port,
        app=PyObservability,
    )
    if settings.env.log:
        if settings.env.log == enums.Log.stdout:
            uvicorn_args["log_config"] = settings.detailed_log_config(debug=settings.env.debug)
        else:
            logs_path = pathlib.Path(settings.env.logs_path)
            log_file = logs_path / f"pyobservability_{datetime.now():%d-%m-%Y}.log"
            logs_path.mkdir(parents=True, exist_ok=True)
            uvicorn_args["log_config"] = settings.detailed_log_config(
                filename=log_file.resolve(), debug=settings.env.debug
            )
    # log_config will take precedence if both log and log_config are set
    if settings.env.log_config:
        uvicorn_args["log_config"] = (
            settings.env.log_config if isinstance(settings.env.log_config, dict) else str(settings.env.log_config)
        )
    uvicorn.run(**uvicorn_args)
