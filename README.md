# PyObservability

![Python][label-pyversion]

**Platform Supported**

![Platform][label-platform]

**Deployments**

[![pypi][label-actions-pypi]][gha_pypi]
[![docker][label-actions-docker]][gha_docker]

[![Pypi][label-pypi]][pypi]
[![Pypi-format][label-pypi-format]][pypi-files]
[![Pypi-status][label-pypi-status]][pypi]

## Kick off

**Recommendations**

- Install `python` [3.11] or above
- Use a dedicated [virtual environment]

**Install PyObservability**
```shell
python -m pip install pyobservability
```

**Initiate - IDE**
```python
import pyobservability


if __name__ == '__main__':
    pyobservability.start()
```

**Initiate - CLI**
```shell
pyobservability start
```

> Use `pyobservability --help` for usage instructions.

**Containerized Deployment**
```shell
docker pull thevickypedia/pyobservability:latest

docker run \
    --name observability \
    -p 8080:80 \
    -v /home/user/config:/config \
    --restart=no \
    thevickypedia/pyobservability
```

## Environment Variables

<details>
<summary><strong>Sourcing environment variables from an env file</strong></summary>

> _By default, `PyObservability` will look for a `.env` file in the current working directory._
> _Other file options (like JSON and YAML) are supported with a custom kwarg or env var `env_file` pointing to the filepath._
</details>

**Mandatory**
- **TARGETS** - Target URLs running `PyNinja` in the following format.
    - `TARGETS='[{"name":"node1","base_url":"http://192.168.1.10:8000","apikey":"token1"},{"name":"node2","base_url":"http://192.168.1.11:8000"}]'`

**Defaults**
- **HOST** - Host IP to run PyObservability. Defaults to `127.0.0.1` or `0.0.0.0`
- **PORT** - Port number to run PyObservability. Defaults to `8080`
- **INTERVAL** - Polling interval to retrieve server information.

**Optional**
- **USERNAME** - Username to authenticate the monitoring page.
- **PASSWORD** - Password to authenticate the monitoring page.
- **TIMEOUT** - Timeout (in seconds) for UI authentication. Defaults to 5m.

**Logging**
> PyObservability uses ``uvicorn`` logger by default. Following options can be used to override the default logger.
- **LOG** - Lazy config to use the default log format. Can either be `file` or `stdout`.
- **DEBUG** - Enables debug level logging. Defaults to `False`.
- **LOGS_PATH** - Directory path to store log files if `LOG` is set to `file`.
- **LOG_CONFIG** - Path to a custom logging configuration file.

**Uptime Kuma**
> Uptime Kuma integration can be enabled by setting the following environment variables.
- **KUMA_URL** - Base URL of the Uptime Kuma server.
- **KUMA_USERNAME** - Username to authenticate with Uptime Kuma.
- **KUMA_PASSWORD** - Password to authenticate with Uptime Kuma.
- **KUMA_TIMEOUT** - Timeout (in seconds) for Uptime Kuma authentication. Defaults to 5s.

## License & copyright

&copy; Vignesh Rao

Licensed under the [MIT License][license]

[//]: # (Labels)

[label-pypi-package]: https://img.shields.io/badge/Pypi%20Package-pyobservability-blue?style=for-the-badge&logo=Python
[label-sphinx-doc]: https://img.shields.io/badge/Made%20with-Sphinx-blue?style=for-the-badge&logo=Sphinx
[label-pyversion]: https://img.shields.io/badge/python-3.11%20%7C%203.12-blue
[label-platform]: https://img.shields.io/badge/Platform-Linux|macOS|Windows-1f425f.svg
[label-actions-pypi]: https://github.com/thevickypedia/PyObservability/actions/workflows/python-publish.yml/badge.svg
[label-pypi]: https://img.shields.io/pypi/v/PyObservability
[label-pypi-format]: https://img.shields.io/pypi/format/PyObservability
[label-pypi-status]: https://img.shields.io/pypi/status/PyObservability
[label-actions-docker]: https://github.com/thevickypedia/PyObservability/actions/workflows/docker.yml/badge.svg

[3.11]: https://docs.python.org/3/whatsnew/3.11.html
[virtual environment]: https://docs.python.org/3/tutorial/venv.html
[gha_pypi]: https://github.com/thevickypedia/PyObservability/actions/workflows/python-publish.yml
[gha_docker]: https://github.com/thevickypedia/PyObservability/actions/workflows/docker.yml
[pypi]: https://pypi.org/project/PyObservability
[pypi-files]: https://pypi.org/project/PyObservability/#files
[license]: https://github.com/thevickypedia/PyObservability/blob/main/LICENSE
