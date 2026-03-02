#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}
CONFIG_PATH="/config/$CONFIG_FILE"

# If config file exists
if [ -f "$CONFIG_PATH" ] && [ "${CONFIG_PATH##*.}" = "json" ]; then
    HOST=${HOST:-$(jq -r '.host // ""' "$CONFIG_PATH")}
    PORT=${PORT:-$(jq -r '.port // ""' "$CONFIG_PATH")}
		ARB="--env $CONFIG_PATH start"
else
		echo "Config file $CONFIG_PATH not found. Using default HOST and PORT."
		ARB="start"
fi

# Defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-80}

echo "Starting PyObservability with ADDRESS=$HOST PORT=$PORT"

pyobservability $ARB
