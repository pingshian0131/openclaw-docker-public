#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.orbstack/bin:$PATH"

# --- Configuration ---
# When running inside cron-dashboard container, host home is at /host_home
HOST_HOME="${HOST_HOME:-/host_home}"
COMPOSE="${OPENCLAW_COMPOSE:-${HOST_HOME}/openclaw-docker/docker-compose.yml}"
RELEASE_NOTES_DIR="${RELEASE_NOTES_DIR:-${HOST_HOME}/Documents/Obsidian/Personal/Releases}"
SERVICES="openclaw-work openclaw-personal"
# Fatal/startup errors only — exclude transient network/websocket errors
ERROR_PATTERNS="FATAL|EACCES|MODULE_NOT_FOUND|ENOENT|Permission denied|Cannot find module|SyntaxError|segfault|OOMKilled"
RESTART_THRESHOLD=2
LOG_SINCE="90m"

has_failure=0

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Collect recent release notes (last 3 days, first 100 lines each)
collect_release_notes() {
  local notes=""
  if [ -d "$RELEASE_NOTES_DIR" ]; then
    while IFS= read -r file; do
      notes+="--- $(basename "$file") ---"$'\n'
      notes+="$(head -100 "$file")"$'\n'$'\n'
    done < <(find "$RELEASE_NOTES_DIR" -name '*.md' -mtime -3 -type f 2>/dev/null | sort -r)
  fi
  echo "$notes"
}

# Try claude CLI with fallback
run_claude() {
  local container="$1"
  local prompt="$2"
  if docker exec "$container" which claude >/dev/null 2>&1; then
    docker exec "$container" claude --print "$prompt" 2>&1
  elif docker exec "$container" which claude-code >/dev/null 2>&1; then
    docker exec "$container" claude-code --print "$prompt" 2>&1
  else
    log "WARNING: No claude CLI found in $container"
    return 1
  fi
}

# --- Main loop ---
for svc in $SERVICES; do
  log "Checking $svc ..."

  # Get container ID
  cid=$(docker compose -f "$COMPOSE" ps -q "$svc" 2>/dev/null || true)
  if [ -z "$cid" ]; then
    log "PROBLEM: $svc — no container found"
    log "Attempting to start $svc ..."
    docker compose -f "$COMPOSE" up -d "$svc" 2>&1
    sleep 15
    cid=$(docker compose -f "$COMPOSE" ps -q "$svc" 2>/dev/null || true)
    if [ -z "$cid" ]; then
      log "FAILED: $svc still has no container after start attempt"
      has_failure=1
      continue
    fi
  fi

  # Check container state
  state=$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo "unknown")
  restart_count=$(docker inspect --format '{{.RestartCount}}' "$cid" 2>/dev/null || echo "0")

  # Check logs for error patterns
  error_lines=$(docker compose -f "$COMPOSE" logs --since "$LOG_SINCE" "$svc" 2>/dev/null \
    | grep -iE "$ERROR_PATTERNS" | tail -50 || true)

  # Determine health
  is_healthy=true
  problems=""

  if [ "$state" != "running" ]; then
    is_healthy=false
    problems+="Container state: $state. "
  fi

  if [ "$restart_count" -gt "$RESTART_THRESHOLD" ]; then
    is_healthy=false
    problems+="Restart count: $restart_count (threshold: $RESTART_THRESHOLD). "
  fi

  if [ -n "$error_lines" ]; then
    is_healthy=false
    problems+="Error patterns found in logs. "
  fi

  if $is_healthy; then
    log "OK: $svc is healthy (state=$state, restarts=$restart_count, no errors)"
    continue
  fi

  # --- Repair phase ---
  log "PROBLEM: $svc — $problems"
  has_failure=1

  # If not running, try to start it first
  if [ "$state" != "running" ]; then
    log "Starting $svc ..."
    docker compose -f "$COMPOSE" up -d "$svc" 2>&1
    sleep 15
    cid=$(docker compose -f "$COMPOSE" ps -q "$svc" 2>/dev/null || true)
    state=$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo "unknown")
    if [ "$state" != "running" ]; then
      log "FAILED: $svc is still not running after restart"
      continue
    fi
  fi

  # Collect context for Claude diagnosis
  recent_logs=$(docker compose -f "$COMPOSE" logs --since "$LOG_SINCE" "$svc" 2>/dev/null | tail -200 || true)
  release_notes=$(collect_release_notes)

  prompt="You are diagnosing an OpenClaw gateway container that has issues after a rebuild.

SERVICE: $svc
PROBLEMS DETECTED: $problems

RECENT CONTAINER LOGS (last ${LOG_SINCE}):
${recent_logs}

ERROR LINES:
${error_lines}"

  if [ -n "$release_notes" ]; then
    prompt+="

RECENT RELEASE NOTES (last 3 days):
${release_notes}"
  fi

  prompt+="

INSTRUCTIONS:
1. Analyze the errors above and identify the root cause.
2. Fix the issue by modifying config files or running commands as needed.
3. If the issue is a permission problem, fix the permissions.
4. If a module is missing, install it.
5. After fixing, verify the fix is in place.
6. Output a brief summary of what you found and fixed."

  log "Running Claude diagnosis on $svc ..."
  if run_claude "$cid" "$prompt"; then
    log "Claude diagnosis completed for $svc"
  else
    log "WARNING: Claude diagnosis failed for $svc"
  fi
done

# --- Summary ---
echo ""
if [ "$has_failure" -eq 0 ]; then
  log "All gateway services are healthy"
  exit 0
else
  log "One or more services had problems — check output above"
  exit 1
fi
