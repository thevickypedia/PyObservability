#!/bin/sh

set -e

# Config file
CONFIG_FILE=${CONFIG_FILE:-settings.json}
CONFIG_PATH="/config/$CONFIG_FILE"

if [ -f "$CONFIG_PATH" ] && [ "${CONFIG_PATH##*.}" = "json" ]; then
    HOST=${HOST:-$(jq -r '.host // ""' "$CONFIG_PATH")}
    PORT=${PORT:-$(jq -r '.port // ""' "$CONFIG_PATH")}
fi

# Defaults
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-80}"

curl -sf -H "X-Health-Check: true" "http://$HOST:$PORT/health" > /dev/null || exit 1
