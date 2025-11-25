import json
import pathlib
import socket
from typing import List

import yaml
from pydantic import BaseModel, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings


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
        extra = "forbid"

    @classmethod
    def from_env_file(cls, filename: pathlib.Path) -> "EnvConfig":
        """Create an instance of EnvConfig from environment file.

        Args:
            filename: Name of the env file.

        Returns:
            EnvConfig:
            Loads the ``EnvConfig`` model.
        """
        # noinspection PyArgumentList
        return cls(_env_file=filename)


def env_loader(**kwargs) -> EnvConfig:
    """Loads environment variables based on filetypes or kwargs.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    # Default to .env if no kwargs were passed
    if not kwargs:
        return EnvConfig.from_env_file(".env")
    # Look for the kwarg env_file and process accordingly
    if env_file := kwargs.get("env_file"):
        env_file = pathlib.Path(env_file)
        assert env_file.is_file(), f"\n\tenv_file: [{env_file.resolve()!r}] does not exist"
        if env_file.suffix.lower() == ".json":
            with open(env_file.filepath) as stream:
                env_data = json.load(stream)
            return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
        elif env_file.suffix.lower() in (".yaml", ".yml"):
            with open(env_file.filepath) as stream:
                env_data = yaml.load(stream, yaml.FullLoader)
            return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
        elif not env_file.suffix or env_file.suffix.lower() in (
            ".text",
            ".txt",
            ".env",
            "",
        ):
            return EnvConfig.from_env_file(env_file.filepath)
        else:
            raise ValueError(
                f"\n\tUnsupported format for {env_file.filepath!r}, "
                "can be one of (.json, .yaml, .yml, .txt, .text, .env)"
            )
    # Load env config with regular kwargs
    return EnvConfig(**kwargs)


env: EnvConfig
