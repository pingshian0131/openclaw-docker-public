"""Seed the database with example tasks.

Run inside the container:
    python seed.py
"""
import sys

from app import create_app
from app.models import Task, db
from app.scheduler import sync_all_jobs

SEED_TASKS = [
    {
        'name': 'System Health Check',
        'description': 'Basic health check — prints OK, uptime, and disk usage',
        'cron_expr': '*/30 * * * *',
        'command': 'echo "OK" && uptime && df -h /data',
        'working_dir': '/data',
        'timeout_secs': 60,
        'enabled': True,
    },
    {
        'name': 'Docker Cleanup',
        'description': 'Remove dangling Docker images and stopped containers older than 7 days',
        'cron_expr': '0 4 * * 0',
        'command': 'docker system prune -f --filter "until=168h"',
        'working_dir': '/',
        'timeout_secs': 300,
        'enabled': True,
    },
    {
        'name': 'Database Backup',
        'description': 'Create a timestamped copy of the cron dashboard SQLite database',
        'cron_expr': '0 3 * * *',
        'command': 'cp /data/cron_dashboard.db /data/backup_$(date +%Y%m%d).db',
        'working_dir': '/data',
        'timeout_secs': 60,
        'enabled': False,
    },
    {
        'name': 'OpenClaw Rebuild',
        'description': 'Fetch latest stable release tag, rebuild openclaw:local image, restart gateway services only (not cron-dashboard)',
        'cron_expr': '0 4 */2 * *',
        'command': '/host_home/openclaw-docker/scripts/rebuild.sh',
        'working_dir': '/host_home',
        'timeout_secs': 3600,
        'enabled': False,
    },
]


def seed():
    app = create_app()
    with app.app_context():
        if Task.query.count() > 0:
            print(f'Database already has {Task.query.count()} tasks, skipping seed.')
            return

        for data in SEED_TASKS:
            task = Task(**data)
            db.session.add(task)
            print(f'  + {task.name}')

        db.session.commit()
        sync_all_jobs()
        print(f'Seeded {len(SEED_TASKS)} tasks.')


if __name__ == '__main__':
    seed()
