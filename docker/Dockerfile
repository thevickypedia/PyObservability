FROM python:3.11-slim

ARG VERSION
ENV VERSION=${VERSION:-latest}
ARG YQ_VERSION
ENV YQ_VERSION=${YQ_VERSION:-v4.49.2}

# Install curl and jq
RUN apt-get update && apt-get install -y jq curl

# Detect architecture and download yq, with fallback to v4.49.2 if latest fails
RUN ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        ARCH="amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        ARCH="arm64"; \
    fi && \
    echo "Downloading yq version: $YQ_VERSION for architecture: $ARCH" && \
    curl -L https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_linux_${ARCH} -o /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

WORKDIR /app

COPY . /temp/pyobservability
# Install from pypi if version is specified, otherwise COPY directly from local
RUN if [ "$VERSION" = "latest" ]; then \
      cd /temp/pyobservability && pip install . && rm -rf /temp/pyobservability; \
    else \
      pip install "pyobservability==$VERSION"; \
    fi

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

HEALTHCHECK --start-period=2s --interval=5s --timeout=3s \
    CMD /healthcheck.sh || exit 1

ENTRYPOINT ["/entrypoint.sh"]
