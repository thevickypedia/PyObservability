#!/bin/sh

set -e

# Config file
CONFIG_PATH=${CONFIG_PATH:-"config"}
mkdir -p ${CONFIG_PATH}

CONFIG_FILE=${CONFIG_FILE:-"$CONFIG_PATH/settings.json"}
PROMETHEUS_FILE=${PROMETHEUS_FILE:-"$CONFIG_PATH/prometheus.yml"}

EXT="${CONFIG_FILE##*.}"

if [[ -z "$EXT" ]]; then
  echo "No extension found!"
  exit 1
fi

# If config file exists
if [ -f "$CONFIG_FILE" ]; then
    case "$EXT" in
        json)
            HOST=${HOST:-$(jq -r '.host // ""' "$CONFIG_FILE")}
            PORT=${PORT:-$(jq -r '.port // ""' "$CONFIG_FILE")}
            PROMETHEUS_ENABLED=${PROMETHEUS_ENABLED:-$(jq -r '.prometheus_enabled // ""' "$CONFIG_FILE")}
            USERNAME=${USERNAME:-$(jq -r '.username // ""' "$CONFIG_FILE")}
            USERNAME=${USERNAME:-$(jq -r '.monitor_username // ""' "$CONFIG_FILE")}
            PASSWORD=${PASSWORD:-$(jq -r '.password // ""' "$CONFIG_FILE")}
            PASSWORD=${PASSWORD:-$(jq -r '.monitor_password // ""' "$CONFIG_FILE")}
            ;;
        yaml|yml)
            HOST=${HOST:-$(yq -r '.host // ""' "$CONFIG_FILE")}
            PORT=${PORT:-$(yq -r '.port // ""' "$CONFIG_FILE")}
            PROMETHEUS_ENABLED=${PROMETHEUS_ENABLED:-$(yq -r '.prometheus_enabled // ""' "$CONFIG_FILE")}
            USERNAME=${USERNAME:-$(yq -r '.username // ""' "$CONFIG_FILE")}
            USERNAME=${USERNAME:-$(yq -r '.monitor_username // ""' "$CONFIG_FILE")}
            PASSWORD=${PASSWORD:-$(yq -r '.password // ""' "$CONFIG_FILE")}
            PASSWORD=${PASSWORD:-$(yq -r '.monitor_password // ""' "$CONFIG_FILE")}
            ;;
    esac
		ARB="--env $CONFIG_FILE start"
else
		echo "Config file $CONFIG_FILE not found. Using default HOST and PORT."
		ARB="start"
fi

# Defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-80}

echo "Starting PyObservability with ADDRESS=$HOST PORT=$PORT"
docker-compose -f docker-compose-server.yml up -d

if [ -z "$PROMETHEUS_ENABLED" ] || [ "$PROMETHEUS_ENABLED" = "null" ] || [ "$PROMETHEUS_ENABLED" = "false" ]; then
    exit 0
fi

export SCRAPE_INTERVAL=${SCRAPE_INTERVAL:-30s}

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

echo "Prometheus config generated at $PROMETHEUS_FILE"
echo "Prometheus metrics enabled. Starting Prometheus container..."
docker-compose -f docker-compose-grafana.yml up -d
