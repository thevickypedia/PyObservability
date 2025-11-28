from enum import StrEnum


class APIEndpoints(StrEnum):
    root = "/"
    ws = "/ws"


class Log(StrEnum):
    file = "file"
    stdout = "stdout"
