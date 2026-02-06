import logging
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from requests.auth import AuthBase
from requests.models import PreparedRequest

from pyobservability.config import settings

LOGGER = logging.getLogger("uvicorn.default")


class BearerAuth(AuthBase):
    # This doc string has URL split into multiple lines
    """Instantiates ``BearerAuth`` object.

    >>> BearerAuth

    Args:
        token: Token for bearer auth.

    References:
        `New Forms of Authentication <https://requests.readthedocs.io/en/latest/user/authentication/#new
        -forms-of-authentication>`__
    """

    def __init__(self, token: str):
        """Initializes the class and assign object members."""
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        """Override built-in.

        Args:
            request: Takes prepared request as an argument.

        Returns:
            PreparedRequest:
            Returns the request after adding the auth header.
        """
        request.headers["authorization"] = "Bearer " + self.token
        return request


@dataclass
class Runner:
    """Runner dataclass to represent a GitHub Actions runner.

    >>> Runner

    """

    id: int
    name: str
    os: str
    status: str
    busy: bool
    labels: List[str]


@dataclass
class Runners:
    """Runners dataclass to represent a collection of GitHub Actions runners.

    >>> Runners

    """

    total: int
    runners: List[Runner]


class GitHub:
    """GitHub object to get runners' information.

    >>> GitHub

    """

    SESSION = requests.Session()

    def __init__(self):
        """Initializes the session and loads the bearer auth with Git token."""
        self.SESSION.auth = BearerAuth(token=settings.env.git_token)

    @staticmethod
    def parser(runners_info: List[Dict[str, Any]]) -> Generator[Runner]:
        """Parses the runners information from the GitHub API response.

        Args:
            runners_info: Runners information as a list of dictionaries from the GitHub API response.

        Yields:
            Runner:
            Yields a Runner object for each runner in the runners' information.
        """
        for runner in runners_info:
            labels = sorted(
                (label["name"] for label in runner["labels"] if label["name"] != "self-hosted"),
                key=lambda s: s.lower(),
            )
            yield Runner(**{**runner, **{"labels": labels}})

    def runners(self) -> Runners | None:
        """Fetches the runners information from the GitHub API.

        Returns:
            Runners | None:
            Returns a Runners object containing the total count and a list of Runner objects,
        """
        try:
            response = self.SESSION.get(f"https://api.github.com/orgs/{settings.env.git_org}/actions/runners")
            response_json = response.json()
        except (requests.RequestException, requests.JSONDecodeError) as error:
            LOGGER.error(error)
            return None
        return Runners(total=response_json["total_count"], runners=list(self.parser(response_json["runners"])))
