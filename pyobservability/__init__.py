"""Module for packaging."""

import sys

from pyobservability.main import start  # noqa: F401
from pyobservability.version import __version__


def _cli() -> None:
    """Starter function to invoke the observability UI via CLI commands.

    **Flags**
        - ``--version | -V``: Prints the version.
        - ``--help | -H``: Prints the help section.
        - ``--env | -E <path>``: Filepath to load environment variables.

    **Commands**
        ``start``: Initiates the PyObservability as a regular script.
    """
    assert sys.argv[0].endswith("pyobservability"), "Invalid commandline trigger!!"
    options = {
        "--version | -V": "Prints the version.",
        "--help | -H": "Prints the help section.",
        "--env | -E <path>": "Filepath to load environment variables.",
        "start": "Initiates the PyObservability as a regular script.",
    }
    # weird way to increase spacing to keep all values monotonic
    _longest_key = len(max(options.keys()))
    _pretext = "\n\t* "
    choices = _pretext + _pretext.join(
        f"{k} {'·' * (_longest_key - len(k) + 8)}→ {v}".expandtabs() for k, v in options.items()
    )
    args = [arg.lower() for arg in sys.argv[1:]]
    try:
        assert len(args) >= 1
    except (IndexError, AttributeError, AssertionError):
        print(f"Cannot proceed without a valid arbitrary command. Please choose from {choices}")
        exit(1)
    env_file = None
    if any(arg in args for arg in ["version", "--version", "-v"]):
        print(f"PyObservability: {__version__}")
        exit(0)
    elif any(arg in args for arg in ["help", "--help", "-h"]):
        print(f"Usage: pyobservability [arbitrary-command]\nOptions (and corresponding behavior):{choices}")
        exit(0)
    elif any(arg in args for arg in ["env", "--env", "E", "-e"]):
        extra_index = next(
            (index for index, arg in enumerate(args) if arg in ["env", "--env", "E", "-e"]),
            None,
        )
        try:
            env_file = sys.argv[extra_index + 2]
        except (IndexError, TypeError):
            print("Cannot proceed without a valid extra environment file path.")
            exit(1)
    elif any(arg in args for arg in ("start",)):
        pass
    else:
        print(f"Unknown Option: {sys.argv[1]}\nArbitrary commands must be one of {choices}")
        exit(1)
    if any(arg in args for arg in ("start",)):
        start(env_file=env_file)
    else:
        print(
            "Insufficient Arguments:\n\tNo command received to initiate the PyObservability. "
            f"Please choose from {choices}"
        )
        exit(1)
