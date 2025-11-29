FROM python:3.11-slim

ARG VERSION
ENV VERSION=${VERSION:-latest}

# Install wget, jq and yq
RUN apt-get update && apt-get install -y wget jq \
  && wget https://github.com/mikefarah/yq/releases/download/v4.15.1/yq_linux_amd64 -O /usr/local/bin/yq \
  && chmod +x /usr/local/bin/yq

WORKDIR /app
# Install from pypi if version is specified, otherwise COPY directly from local
COPY . .
RUN if [ "$VERSION" = "latest" ]; then pip install . ; else pip install "pyobservability==$VERSION" ; fi

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --start-period=2s --interval=5s --timeout=3s \
    CMD /healthcheck.sh || exit 1

ENTRYPOINT ["/entrypoint.sh"]
