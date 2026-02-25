# OpenClaw Docker

[繁體中文](README.zh-TW.md) | English

A Docker Compose setup for running multiple [OpenClaw](https://github.com/anthropics/claude-code) gateway environments with a built-in **Cron Dashboard** for automated task management.

## Architecture

```
docker-compose.yml
├── openclaw-work        Gateway (ports 18791-18792)
├── openclaw-personal    Gateway (ports 18793-18794)
├── cli-work             Interactive CLI
├── cli-personal         Interactive CLI
└── cron-dashboard       Flask web UI (port 18799)
```

| Service | Description | Ports |
|---------|-------------|-------|
| `openclaw-work` | Work environment gateway | 18791, 18792 |
| `openclaw-personal` | Personal environment gateway | 18793, 18794 |
| `cli-work` | Work environment CLI (interactive) | — |
| `cli-personal` | Personal environment CLI (interactive) | — |
| `cron-dashboard` | Cron job management web UI | 18799 |

## Prerequisites

- **Docker** and **Docker Compose** (v2)
- **OpenClaw base image** — built locally as `openclaw:local`. Follow the [OpenClaw build instructions](https://github.com/anthropics/claude-code) to create this image.
- **Claude Code credentials** at `~/.claude/.credentials.json`

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/anthropics/openclaw-docker.git
cd openclaw-docker

# 2. Copy and edit the environment file
cp .env.example .env
# Edit .env — fill in your gateway tokens and dashboard password

# 3. Build and start all services
docker compose up -d --build

# 4. (Optional) Seed the cron dashboard with example tasks
docker compose exec cron-dashboard python seed.py
```

The cron dashboard is now available at **http://localhost:18799**.

## Configuration

### Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `OPENCLAW_WORK_TOKEN` | Gateway auth token for work environment |
| `OPENCLAW_PERSONAL_TOKEN` | Gateway auth token for personal environment |
| `OPENCLAW_IMAGE` | Base image name (default: `openclaw:local`) |
| `CRON_DASHBOARD_PASSWORD` | Dashboard login password |
| `CRON_DASHBOARD_SECRET_KEY` | Flask session secret key |

### Volume Mounts

Each gateway mounts directories from your host into the container:

| Service | Host Path | Container Path | Purpose |
|---------|-----------|----------------|---------|
| `openclaw-work` | `~/work` | `/home/node/work` | Work projects |
| `openclaw-personal` | `~/projects` | `/home/node/projects` | Personal projects |
| Both | `~/.openclaw-*` | `/home/node/.openclaw` | OpenClaw config |
| Both | `~/.claude/.credentials.json` | `/home/node/.claude/.credentials.json` | Claude auth (read-only) |

Edit `docker-compose.yml` to mount your own directories. For example:

```yaml
volumes:
  - ~/.openclaw-work:/home/node/.openclaw
  - ~/.claude/.credentials.json:/home/node/.claude/.credentials.json:ro
  - ~/my-company-repo:/home/node/my-company-repo    # <-- add your own
```

## Customization

### Adding Python Packages

If your Claude Code skills need Python dependencies, edit `Dockerfile.openclaw` — there are commented-out instructions showing how to install pip and packages.

### Changing Ports

Update the `ports` mapping in `docker-compose.yml`. The left side is the host port, the right side is the container port (keep `18789`/`18790` on the right).

### Single Gateway Setup

If you only need one gateway, remove the `openclaw-personal` and `cli-personal` services from `docker-compose.yml`.

## Cron Dashboard

A web-based cron job manager built with Flask + APScheduler.

**Features:**
- Create, edit, and delete scheduled tasks with cron expressions
- Manual trigger for any task
- Real-time cron expression validator
- Execution logs with stdout/stderr capture
- Simple password authentication

**Pre-seeded example tasks:**
- System Health Check (every 30 minutes)
- Docker Cleanup (weekly)
- Database Backup (daily, disabled by default)

You can add your own tasks through the web UI at `http://localhost:18799`.

## Common Commands

```bash
# Start all services
docker compose up -d

# Rebuild after Dockerfile changes
docker compose up -d --build

# View logs
docker compose logs -f openclaw-work
docker compose logs -f cron-dashboard

# Shell into a container
docker exec -it $(docker compose ps -q openclaw-work) sh

# Stop all services
docker compose down
```

## License

[MIT](LICENSE)
