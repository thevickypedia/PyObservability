FROM python:3.11-slim

ARG VERSION
ENV VERSION=${VERSION:-latest}

# Install curl and jq
RUN apt-get update && apt-get install -y jq curl

WORKDIR /app

COPY . /temp/pyobservability
# Install from pypi if version is specified, otherwise COPY directly from local
RUN if [ "$VERSION" = "latest" ]; then \
      cd /temp/pyobservability && pip install --upgrade pip uv && uv pip install . --system && rm -rf /temp/pyobservability; \
    else \
      pip install --upgrade pip uv && uv pip install "pyobservability==$VERSION" --system; \
    fi

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

HEALTHCHECK --start-period=2s --interval=5s --timeout=3s \
    CMD /healthcheck.sh || exit 1

ENTRYPOINT ["/entrypoint.sh"]
