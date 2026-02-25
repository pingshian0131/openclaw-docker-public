# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docker Compose setup that runs two OpenClaw gateway environments (work & personal) with a Flask-based cron dashboard for automated task management (backups, image rebuilds, cleanup).

## Architecture

```
docker-compose.yml
├── openclaw-work        (gateway, port 18791-18792)
├── openclaw-personal    (gateway, port 18793-18794)
├── cli-work             (interactive CLI)
├── cli-personal         (interactive CLI)
└── cron-dashboard       (Flask web UI, port 18799)
```

- **OpenClaw services**: Built from `Dockerfile.openclaw` which extends the base `openclaw:local` image with Claude Code CLI. PATH is set in the Dockerfile.
- **Cron dashboard**: Flask 3.1 + APScheduler + SQLite. Has Docker CLI, docker-compose plugin, git, and rclone installed for executing host-level tasks via Docker socket.

## Common Commands

```bash
# Start all services
docker compose up -d

# Rebuild after base image or Dockerfile.openclaw changes
docker compose up -d --build

# Rebuild only cron-dashboard
docker compose up -d --build cron-dashboard

# View logs
docker compose logs -f openclaw-work
docker compose logs -f cron-dashboard

# Shell into a container
docker exec -it $(docker compose ps -q openclaw-work) sh
```

## Cron Dashboard (cron-dashboard/)

Flask app with this structure:
- `app/__init__.py` — App factory, registers blueprints, starts scheduler
- `app/models.py` — `Task` and `ExecutionLog` SQLAlchemy models
- `app/scheduler.py` — APScheduler integration, task execution with subprocess, log capture (512KB max), concurrency guard
- `app/routes/` — Blueprints: `dashboard`, `tasks` (CRUD), `logs` (paginated), `api` (toggle/run/validate)
- `app/auth.py` — Simple password-based session auth
- `seed.py` — Example tasks (health check, docker cleanup, database backup)

Database is SQLite at `/data/cron_dashboard.db` (persisted via `cron-dashboard-data` volume).

## Environment Variables

Defined in `.env` (see `.env.example`):
- `OPENCLAW_WORK_TOKEN` / `OPENCLAW_PERSONAL_TOKEN` — Gateway auth tokens
- `CRON_DASHBOARD_PASSWORD` — Dashboard login password
- `CRON_DASHBOARD_SECRET_KEY` — Flask session secret
- `OPENCLAW_IMAGE` — Base image name (default: `openclaw:local`)

## Key Patterns

- Host home directory is mounted as `/host_home` in cron-dashboard for executing backup/rebuild scripts.
- `~/.claude/.credentials.json` is mounted read-only into gateway containers for Claude Code auth.
- All containers use `TZ: Asia/Taipei`.
