from enum import StrEnum


class APIEndpoints(StrEnum):
    """API endpoints for all the routes.

    >>> APIEndpoints

    """

    health = "/health"
    root = "/"
    ws = "/ws"


class Log(StrEnum):
    """Log output options.

    >>> Log

    """

    file = "file"
    stdout = "stdout"
