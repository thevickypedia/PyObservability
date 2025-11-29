FROM python:3.11-slim

ARG VERSION
ENV VERSION=${VERSION:-latest}

# Install wget, jq and yq
RUN apt-get update && apt-get install -y wget jq
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        ARCH="amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        ARCH="arm64"; \
    fi && \
    YQ_VERSION=$(curl -s https://api.github.com/repos/mikefarah/yq/releases/latest | jq -r .tag_name) && \
    echo "Downloading yq version: $YQ_VERSION for architecture: $ARCH" && \
    wget https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/yq_linux_${ARCH} -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

WORKDIR /app

COPY . /temp/pyobservability
# Install from pypi if version is specified, otherwise COPY directly from local
RUN if [ "$VERSION" = "latest" ]; then \
      cd /temp/pyobservability && pip install . && rm -rf /temp/pyobservability; \
    else \
      pip install "pyobservability==$VERSION"; \
    fi

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --start-period=2s --interval=5s --timeout=3s \
    CMD /healthcheck.sh || exit 1

ENTRYPOINT ["/entrypoint.sh"]
