#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}
CONFIG_PATH="/config/$CONFIG_FILE"

EXT="${CONFIG_PATH##*.}"

# If config file exists
if [ -f "$CONFIG_PATH" ]; then
    case "$EXT" in
        json)
            HOST=${HOST:-$(jq -r '.host // empty' "$CONFIG_PATH")}
            PORT=${PORT:-$(jq -r '.port // empty' "$CONFIG_PATH")}
            ;;
        yaml|yml)
            HOST=${HOST:-$(yq -r '.host // empty' "$CONFIG_PATH")}
            PORT=${PORT:-$(yq -r '.port // empty' "$CONFIG_PATH")}
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

pyobservability $ARB
