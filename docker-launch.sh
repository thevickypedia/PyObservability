#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}
CONFIG_PATH="config/$CONFIG_FILE"
PROMETHEUS_FILE="config/prometheus.yml"

# If config file exists
if [ -f "$CONFIG_PATH" ] && [ "${CONFIG_PATH##*.}" = "json" ]; then
    HOST=${HOST:-$(jq -r '.host // ""' "$CONFIG_PATH")}
    PORT=${PORT:-$(jq -r '.port // ""' "$CONFIG_PATH")}
    USERNAME=${USERNAME:-$(jq -r '.username // ""' "$CONFIG_PATH")}
    USERNAME=${USERNAME:-$(jq -r '.monitor_username // ""' "$CONFIG_PATH")}
    PASSWORD=${PASSWORD:-$(jq -r '.password // ""' "$CONFIG_PATH")}
    PASSWORD=${PASSWORD:-$(jq -r '.monitor_password // ""' "$CONFIG_PATH")}
    PROMETHEUS_ENABLED=${PROMETHEUS_ENABLED:-$(jq -r '.prometheus_enabled // ""' "$CONFIG_PATH")}
		ARB="--env $CONFIG_PATH start"
else
		echo "Config file $CONFIG_PATH not found. Using default HOST and PORT."
		ARB="start"
fi

# Defaults
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-80}"

echo "Starting PyObservability with ADDRESS=$HOST PORT=$PORT"
docker-compose -f docker-compose-server.yml up -d

if [ ! "${PROMETHEUS_ENABLED,,}" = "true" ]; then
    exit 0
fi

export SCRAPE_INTERVAL="${SCRAPE_INTERVAL:-30s}"

# Start building the file content
cat <<EOF > "$PROMETHEUS_FILE"
global:
    scrape_interval: $SCRAPE_INTERVAL

scrape_configs:
    - job_name: "pyobservability"
EOF

# Conditionally add basic_auth only if both USERNAME and PASSWORD are non-empty
if [[ -n "$USERNAME" && -n "$PASSWORD" ]]; then
    cat <<EOF >> "$PROMETHEUS_FILE"
      basic_auth:
          username: $USERNAME
          password: $PASSWORD
EOF
fi

# Add the static_configs section
cat <<EOF >> "$PROMETHEUS_FILE"
      static_configs:
          - targets: ["host.docker.internal:$PORT"]
EOF

echo "Prometheus metrics enabled. Starting Prometheus container..."
docker-compose -f docker-compose-grafana.yml up -d
