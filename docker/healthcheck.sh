#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}   # default: settings.json
CONFIG_PATH="/config/$CONFIG_FILE"

# If config file is JSON
if [ -f "$CONFIG_PATH" ] && [ "${CONFIG_PATH##*.}" = "json" ]; then
    HOST=${HOST:-$(jq -r '.host // empty' "$CONFIG_PATH")}
    PORT=${PORT:-$(jq -r '.port // empty' "$CONFIG_PATH")}
fi

# If config file is YAML
if [ -f "$CONFIG_PATH" ] && [[ "${CONFIG_PATH##*.}" = "yaml" || "${CONFIG_PATH##*.}" = "yml" ]]; then
    HOST=${HOST:-$(yq -r '.host // empty' "$CONFIG_PATH")}
    PORT=${PORT:-$(yq -r '.port // empty' "$CONFIG_PATH")}
fi

# Defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-80}

curl -sf http://$HOST:$PORT/health > /dev/null || exit 1
