#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.orbstack/bin:$PATH"

# TODO: Set OPENCLAW_REPO to the path where you cloned the openclaw source repo
REPO="${OPENCLAW_REPO:-$HOME/Documents/openclaw}"

# TODO: Set OPENCLAW_COMPOSE to the path of your docker-compose.yml
COMPOSE="${OPENCLAW_COMPOSE:-$HOME/openclaw-docker/docker-compose.yml}"

LOG="/tmp/openclaw-rebuild.log"

echo "=== OpenClaw rebuild started at $(date) ===" | tee -a "$LOG"

# Fetch tags and checkout latest stable release
git -C "$REPO" fetch --tags 2>&1 | tee -a "$LOG"
LATEST_TAG=$(git -C "$REPO" tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
CURRENT_TAG=$(git -C "$REPO" describe --tags --exact-match 2>/dev/null || echo "none")

if [ "$LATEST_TAG" = "$CURRENT_TAG" ]; then
  echo "Already on latest release $LATEST_TAG, skipping rebuild." | tee -a "$LOG"
  echo "=== OpenClaw rebuild skipped at $(date) ===" | tee -a "$LOG"
  exit 0
fi

echo "Updating from $CURRENT_TAG to $LATEST_TAG" | tee -a "$LOG"
git -C "$REPO" checkout "$LATEST_TAG" 2>&1 | tee -a "$LOG"

# Build
docker build -t openclaw:local -f "$REPO/Dockerfile" "$REPO" 2>&1 | tee -a "$LOG"

# Restart only gateway services — do NOT restart cron-dashboard
docker compose -f "$COMPOSE" up -d --build openclaw-work openclaw-personal 2>&1 | tee -a "$LOG"

echo "=== OpenClaw rebuild completed at $(date) ===" | tee -a "$LOG"
