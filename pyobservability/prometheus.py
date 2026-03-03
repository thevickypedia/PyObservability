import secrets
from typing import Any, Dict, NoReturn

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)

from pyobservability.config import settings

security = HTTPBasic()

# Collector registry and dynamic gauges store
registry = CollectorRegistry()
gauges: Dict[str, Gauge] = {}


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> None | NoReturn:
    """Verifies credentials for prometheus endpoint.

    Args:
        credentials: HTTP basic auth credentials.
    """
    correct_username = secrets.compare_digest(credentials.username, settings.env.username)
    correct_password = secrets.compare_digest(credentials.password, settings.env.password)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def flatten_payload(node: str, data: dict, parent_keys: list[str] = None) -> None:
    """Recursively traverse the payload and push numeric values to Prometheus.

    Handles nested dicts and lists of numbers or dicts.

    Args:
        node: The node identifier for labeling metrics.
        data: The current level of the payload to process.
        parent_keys: List of parent keys to build metric names from.
    """
    for key, value in data.items():
        metric_path = parent_keys or [] + [key]

        if isinstance(value, (int, float)):
            # numeric value → create/update gauge
            metric_name = "_".join(metric_path).lower()
            if metric_name not in gauges:
                gauges[metric_name] = Gauge(metric_name, f"Metric for {metric_name}", ["node"], registry=registry)
            gauges[metric_name].labels(node=node).set(value)

        elif isinstance(value, dict):
            flatten_payload(node, value, metric_path)

        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, (int, float)):
                    metric_name = "_".join(metric_path + [str(idx)]).lower()
                    if metric_name not in gauges:
                        gauges[metric_name] = Gauge(
                            metric_name, f"Metric for {metric_name}", ["node"], registry=registry
                        )
                    gauges[metric_name].labels(node=node).set(item)
                elif isinstance(item, dict):
                    flatten_payload(node, item, metric_path + [str(idx)])


def update_metrics(payload: Dict[str, Any]) -> None:
    """Push metrics dynamically from a payload.

    Args:
        payload: The payload containing metrics data, expected to have a "node" key and various nested metrics.
    """
    node = payload.get("node", "unknown")
    flatten_payload(node, payload)


async def metrics_endpoint():
    """Endpoint for Prometheus to scrape metrics."""
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
