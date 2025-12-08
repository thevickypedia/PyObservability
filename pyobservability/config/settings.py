import json
import os
import pathlib
import socket
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field, FilePath, HttpUrl, PositiveInt
from pydantic.aliases import AliasChoices
from pydantic_settings import BaseSettings

from pyobservability.config import enums


def detailed_log_config(filename: str | None = None, debug: bool = False) -> Dict[str, Any]:
    """Generate a detailed logging configuration.

    Args:
        filename: Optional log file name. If None, logs to stdout.
        debug: If True, sets log level to DEBUG, else INFO.

    Returns:
        Dict[str, Any]:
        Returns the logging configuration dictionary.
    """
    if filename:
        log_handler = {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": filename,
            "mode": "a",
        }
    else:
        log_handler = {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    level = "DEBUG" if debug else "INFO"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
                "datefmt": "%b-%d-%Y %I:%M:%S %p",
            }
        },
        "handlers": {"default": log_handler},
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": level},
            "uvicorn.error": {"handlers": ["default"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": level, "propagate": False},
            "uvicorn.default": {"handlers": ["default"], "level": level, "propagate": False},
        },
        "root": {"handlers": ["default"], "level": level},
    }


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
        """Customize the order of settings sources."""
        # Precedence (last wins):
        # env < dotenv < file secrets < init
        return (
            env_settings,
            dotenv_settings,
            file_secret_settings,
            init_settings,
        )


class MonitorTarget(BaseModel):
    """Model representing a monitoring target.

    >>> MonitorTarget

    """

    name: str
    base_url: HttpUrl
    apikey: str


def alias_choices(variable: str) -> AliasChoices:
    """Custom alias choices for environment variables for GitHub.

    Args:
        variable: Variable name.

    Returns:
        AliasChoices:
        Returns the alias choices for the variable.
    """
    choices = (variable, variable.lower(), f"MONITOR_{variable}", f"monitor_{variable.lower()}")
    return AliasChoices(*choices)


class EnvConfig(PydanticEnvConfig):
    """Configuration settings for the server.

    >>> EnvConfig

    """

    host: str = Field(socket.gethostbyname("localhost") or "0.0.0.0", validation_alias=alias_choices("HOST"))
    port: PositiveInt = Field(8080, validation_alias=alias_choices("PORT"))

    targets: List[MonitorTarget] = Field(..., validation_alias=alias_choices("TARGETS"))
    interval: PositiveInt = Field(3, validation_alias=alias_choices("INTERVAL"))

    log: enums.Log | None = None
    logs_path: str = "logs"
    debug: bool = False
    log_config: Dict[str, Any] | FilePath | None = None

    username: str | None = Field(None, validation_alias=alias_choices("USERNAME"))
    password: str | None = Field(None, validation_alias=alias_choices("PASSWORD"))
    timeout: PositiveInt = Field(300, validation_alias=alias_choices("TIMEOUT"))

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        extra = "forbid"
        hide_input_in_errors = True

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
    if env_file := kwargs.get("env_file") or os.getenv("env_file"):
        env_file = pathlib.Path(env_file)
        assert env_file.is_file(), f"\n\tenv_file: [{env_file.resolve()!r}] does not exist"
        if env_file.suffix.lower() == ".json":
            with env_file.open() as stream:
                env_data = json.load(stream)
            return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
        if env_file.suffix.lower() in (".yaml", ".yml"):
            with env_file.open() as stream:
                env_data = yaml.load(stream, yaml.FullLoader)
            return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
        if not env_file.suffix or env_file.suffix.lower() in (
            ".text",
            ".txt",
            ".env",
            "",
        ):
            return EnvConfig.from_env_file(env_file)
        raise ValueError(
            f"\n\tUnsupported format for {env_file!r}, " "can be one of (.json, .yaml, .yml, .txt, .text, .env)"
        )
    # Load env config with regular kwargs
    return EnvConfig(**kwargs)


env: EnvConfig
targets_by_url: Dict[str, Dict[str, str]]
