#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}
CONFIG_PATH="config/$CONFIG_FILE"

EXT="${CONFIG_PATH##*.}"

if [[ -z "$EXT" ]]; then
  echo "No extension found!"
  exit 1
fi

# If config file exists
if [ -f "$CONFIG_PATH" ]; then
    case "$EXT" in
        json)
            HOST=${HOST:-$(jq -r '.host // ""' "$CONFIG_PATH")}
            PORT=${PORT:-$(jq -r '.port // ""' "$CONFIG_PATH")}
            PROMETHEUS_ENABLED=${PROMETHEUS_ENABLED:-$(jq -r '.prometheus_enabled // ""' "$CONFIG_PATH")}
            USERNAME=${USERNAME:-$(jq -r '.username // ""' "$CONFIG_PATH")}
            USERNAME=${USERNAME:-$(jq -r '.monitor_username // ""' "$CONFIG_PATH")}
            PASSWORD=${PASSWORD:-$(jq -r '.password // ""' "$CONFIG_PATH")}
            PASSWORD=${PASSWORD:-$(jq -r '.monitor_password // ""' "$CONFIG_PATH")}
            ;;
        yaml|yml)
            HOST=${HOST:-$(yq -r '.host // ""' "$CONFIG_PATH")}
            PORT=${PORT:-$(yq -r '.port // ""' "$CONFIG_PATH")}
            PROMETHEUS_ENABLED=${PROMETHEUS_ENABLED:-$(yq -r '.prometheus_enabled // ""' "$CONFIG_PATH")}
            USERNAME=${USERNAME:-$(yq -r '.username // ""' "$CONFIG_PATH")}
            USERNAME=${USERNAME:-$(yq -r '.monitor_username // ""' "$CONFIG_PATH")}
            PASSWORD=${PASSWORD:-$(yq -r '.password // ""' "$CONFIG_PATH")}
            PASSWORD=${PASSWORD:-$(yq -r '.monitor_password // ""' "$CONFIG_PATH")}
            ;;
    esac
		ARB="--env $CONFIG_PATH start"
else
		echo "Config file $CONFIG_PATH not found. Using default HOST and PORT."
		ARB="start"
fi

# Defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-80}

echo "Starting PyObservability with ADDRESS=$HOST PORT=$PORT"
docker-compose -f docker-compose-server.yml up -d

if [ "${PROMETHEUS_ENABLED,,}" = "true" ]; then
  echo "Prometheus metrics enabled. Starting Prometheus container..."
  docker-compose -f docker-compose-grafana.yml up -d
fi
