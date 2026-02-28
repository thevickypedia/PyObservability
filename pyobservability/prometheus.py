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


# TODO: Generate `prometheus.yml` file
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> None | NoReturn:
    """Verifies credentials for prometheus endpoint.

    Args:
        credentials: HTTP basic auth credentials.

    Examples:
        ```yaml
            global:
              scrape_interval: 30s

            scrape_configs:
              - job_name: "pyobservability"
                basic_auth:
                  username: <settings.env.username>
                  password: <settings.env.password>
                static_configs:
                    # TODO: Identify container and then generate this or probably all in ONE
                    # host: <0.0.0.0 || host.docker.internal>
                  - targets: ["host:<settings.env.port>"]
        ```
    """
    correct_username = secrets.compare_digest(credentials.username, settings.env.username)
    correct_password = secrets.compare_digest(credentials.password, settings.env.password)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


registry = CollectorRegistry()

# TODO: Look into parametrizing all the hard coded values (possible schema expose from PyNinja server)
# System info gauge with labels (static, always 1)
system_info = Gauge(
    "system_info",
    "System static info labels",
    ["node", "system", "architecture", "cpu_name", "gpu_name", "python_version", "pyninja_version"],
)

# CPU usage per core
cpu_usage_percent = Gauge("cpu_usage_percent", "CPU usage percent per core", ["node", "core"])

# Memory gauges
memory_total_bytes = Gauge("memory_total_bytes", "Total memory in bytes", ["node"])
memory_used_bytes = Gauge("memory_used_bytes", "Used memory in bytes", ["node"])
memory_available_bytes = Gauge("memory_available_bytes", "Available memory in bytes", ["node"])
memory_free_bytes = Gauge("memory_free_bytes", "Free memory in bytes", ["node"])
memory_active_bytes = Gauge("memory_active_bytes", "Active memory in bytes", ["node"])
memory_inactive_bytes = Gauge("memory_inactive_bytes", "Inactive memory in bytes", ["node"])
memory_wired_bytes = Gauge("memory_wired_bytes", "Wired memory in bytes", ["node"])

# Swap info
swap_total_bytes = Gauge("swap_total_bytes", "Total swap memory in bytes", ["node"])
swap_used_bytes = Gauge("swap_used_bytes", "Used swap memory in bytes", ["node"])
swap_free_bytes = Gauge("swap_free_bytes", "Free swap memory in bytes", ["node"])
swap_percent = Gauge("swap_percent", "Swap usage percent", ["node"])
swap_sin_bytes = Gauge("swap_sin_bytes", "Swap in bytes", ["node"])
swap_sout_bytes = Gauge("swap_sout_bytes", "Swap out bytes", ["node"])

# Load averages
load_avg_1m = Gauge("load_average_1m", "Load average 1 minute", ["node"])
load_avg_5m = Gauge("load_average_5m", "Load average 5 minutes", ["node"])
load_avg_15m = Gauge("load_average_15m", "Load average 15 minutes", ["node"])

# Disk info per disk
disk_total_bytes = Gauge("disk_total_bytes", "Total disk size in bytes", ["node", "disk_name"])
disk_used_bytes = Gauge("disk_used_bytes", "Used disk size in bytes", ["node", "disk_name"])
disk_free_bytes = Gauge("disk_free_bytes", "Free disk size in bytes", ["node", "disk_name"])


def update_metrics(payload: Dict[str, Any]) -> None:
    """Push metrics to prometheus."""
    node = payload["name"]
    metrics = payload["metrics"]

    # Update static info metric with labels (value=1)
    system_info.labels(
        node=node,
        system=metrics.get("system", ""),
        architecture=metrics.get("architecture", ""),
        cpu_name=metrics.get("cpu_name", ""),
        gpu_name=metrics.get("gpu_name", ""),
        python_version=metrics.get("python_version", ""),
        pyninja_version=metrics.get("pyninja_version", ""),
    ).set(1)

    # Update CPU usage per core
    for core_index, usage in enumerate(metrics.get("cpu_usage", [])):
        cpu_usage_percent.labels(node=node, core=str(core_index)).set(usage)

    # Update memory info
    mem = metrics.get("memory_info", {})
    memory_total_bytes.labels(node=node).set(mem.get("total", 0))
    memory_used_bytes.labels(node=node).set(mem.get("used", 0))
    memory_available_bytes.labels(node=node).set(mem.get("available", 0))
    memory_free_bytes.labels(node=node).set(mem.get("free", 0))
    memory_active_bytes.labels(node=node).set(mem.get("active", 0))
    memory_inactive_bytes.labels(node=node).set(mem.get("inactive", 0))
    memory_wired_bytes.labels(node=node).set(mem.get("wired", 0))

    # Swap info
    swap = metrics.get("swap_info", {})
    swap_total_bytes.labels(node=node).set(swap.get("total", 0))
    swap_used_bytes.labels(node=node).set(swap.get("used", 0))
    swap_free_bytes.labels(node=node).set(swap.get("free", 0))
    swap_percent.labels(node=node).set(swap.get("percent", 0))
    swap_sin_bytes.labels(node=node).set(swap.get("sin", 0))
    swap_sout_bytes.labels(node=node).set(swap.get("sout", 0))

    # Load averages
    load = metrics.get("load_averages", {})
    load_avg_1m.labels(node=node).set(load.get("m1", 0))
    load_avg_5m.labels(node=node).set(load.get("m5", 0))
    load_avg_15m.labels(node=node).set(load.get("m15", 0))

    # Disk info
    disks = metrics.get("disk_info", [])
    for disk in disks:
        disk_name = disk.get("name", "unknown")
        disk_total_bytes.labels(node=node, disk_name=disk_name).set(disk.get("total", 0))
        disk_used_bytes.labels(node=node, disk_name=disk_name).set(disk.get("used", 0))
        disk_free_bytes.labels(node=node, disk_name=disk_name).set(disk.get("free", 0))


async def metrics_endpoint():
    """Endpoint for prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
