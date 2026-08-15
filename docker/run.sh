#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

XAUTH_FILE="/tmp/.docker.xauth"
DISPLAY="${DISPLAY:-:0}"

touch "$XAUTH_FILE"
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH_FILE" nmerge -

cd "$PROJECT_DIR"
docker compose -f docker/docker-compose.yml up --build dev
