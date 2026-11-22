#!/usr/bin/env bash
# Wait until the app in the given container answers Streamlit's health endpoint.
# Usage: wait-for-health.sh <container-name> [url]
set -euo pipefail

container="$1"
url="${2:-http://localhost:8501/_stcore/health}"

for _ in $(seq 1 30); do
  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "App is healthy at $url"
    exit 0
  fi
  sleep 2
done

echo "::error::App did not become healthy within 60s"
docker logs "$container" || true
exit 1
