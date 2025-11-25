import os
import socket
from pydantic import BaseModel, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings
from typing import List


class PydanticEnvConfig(BaseSettings):
    """Pydantic BaseSettings with custom order for loading environment variables.

    >>> PydanticEnvConfig

    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Order: dotenv, env, init, secrets files."""
        return dotenv_settings, env_settings, init_settings, file_secret_settings


class MonitorTarget(BaseModel):
    name: str
    base_url: HttpUrl
    apikey: str


class EnvConfig(PydanticEnvConfig):
    """Configuration settings for the server.

    >>> EnvConfig

    """

    host: str = socket.gethostbyname("localhost") or "0.0.0.0"
    port: PositiveInt = 8080

    monitor_targets: List[MonitorTarget]
    poll_interval: PositiveInt = 3

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = os.getenv("env_file") or os.getenv("ENV_FILE") or ".env"
        extra = "forbid"


env = EnvConfig()
