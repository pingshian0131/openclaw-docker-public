import logging
import os
import subprocess
import threading
from datetime import datetime, timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_app = None


def init_scheduler(app):
    global _app
    _app = app

    tz = app.config.get('TZ', 'Asia/Taipei')
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:////data/apscheduler_jobs.db'),
    }
    scheduler.configure(jobstores=jobstores, timezone=tz)

    with app.app_context():
        sync_all_jobs()

    scheduler.add_job(
        _cleanup_old_logs, 'cron', hour=2, minute=0,
        id='__log_retention__', replace_existing=True,
    )
    scheduler.start()
    logger.info('Scheduler started with timezone %s', tz)


def sync_all_jobs():
    from app.models import Task

    tasks = Task.query.filter_by(enabled=True).all()
    existing_job_ids = {job.id for job in scheduler.get_jobs()}
    task_job_ids = set()

    for task in tasks:
        job_id = f'task_{task.id}'
        task_job_ids.add(job_id)
        try:
            trigger = CronTrigger.from_crontab(task.cron_expr, timezone=_app.config.get('TZ', 'Asia/Taipei'))
            scheduler.add_job(
                _execute_task, trigger=trigger, id=job_id,
                replace_existing=True, kwargs={'task_id': task.id},
            )
        except ValueError as e:
            logger.error('Invalid cron expression for task %d (%s): %s', task.id, task.name, e)

    for job_id in existing_job_ids - task_job_ids - {'__log_retention__'}:
        scheduler.remove_job(job_id)

    logger.info('Synced %d jobs (%d removed)', len(task_job_ids), len(existing_job_ids - task_job_ids - {'__log_retention__'}))


def add_job(task):
    job_id = f'task_{task.id}'
    try:
        trigger = CronTrigger.from_crontab(task.cron_expr, timezone=_app.config.get('TZ', 'Asia/Taipei'))
        scheduler.add_job(
            _execute_task, trigger=trigger, id=job_id,
            replace_existing=True, kwargs={'task_id': task.id},
        )
    except ValueError as e:
        logger.error('Failed to add job for task %d: %s', task.id, e)


def remove_job(task_id):
    job_id = f'task_{task_id}'
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def run_now(task_id):
    """Trigger a task immediately in a background thread."""
    t = threading.Thread(target=_execute_task, kwargs={'task_id': task_id, 'trigger_type': 'manual'})
    t.daemon = True
    t.start()


def _execute_task(task_id, trigger_type='scheduled'):
    with _app.app_context():
        from app.models import ExecutionLog, Task, db

        task = Task.query.get(task_id)
        if not task:
            logger.warning('Task %d not found, skipping execution', task_id)
            return

        # Concurrency guard: skip if already running
        running = ExecutionLog.query.filter_by(task_id=task.id, status='running').first()
        if running:
            logger.warning('Task %d (%s) is already running, skipping', task.id, task.name)
            return

        max_output = _app.config.get('MAX_LOG_OUTPUT_BYTES', 524288)

        log_entry = ExecutionLog(
            task_id=task.id,
            trigger_type=trigger_type,
            started_at=datetime.now(),
            status='running',
        )
        db.session.add(log_entry)
        task.last_run_at = log_entry.started_at
        task.last_run_status = 'running'
        db.session.commit()

        env = os.environ.copy()
        env['HOME'] = '/host_home'
        env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        env['DOCKER_HOST'] = 'unix:///var/run/docker.sock'
        env['DOCKER_CONFIG'] = '/tmp/.docker'  # ignore host's orbstack context

        try:
            result = subprocess.run(
                task.command, shell=True,
                capture_output=True, text=True,
                timeout=task.timeout_secs,
                cwd=task.working_dir,
                env=env,
            )
            log_entry.exit_code = result.returncode
            log_entry.stdout = result.stdout[:max_output]
            log_entry.stderr = result.stderr[:max_output]
            log_entry.status = 'success' if result.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired as e:
            log_entry.status = 'timeout'
            log_entry.stdout = (e.stdout or b'').decode('utf-8', errors='replace')[:max_output]
            log_entry.stderr = (e.stderr or b'').decode('utf-8', errors='replace')[:max_output]
        except Exception as e:
            log_entry.status = 'failed'
            log_entry.stderr = str(e)

        log_entry.finished_at = datetime.now()
        log_entry.duration_secs = (log_entry.finished_at - log_entry.started_at).total_seconds()
        task.last_run_status = log_entry.status
        task.last_run_duration_secs = log_entry.duration_secs
        db.session.commit()

        logger.info(
            'Task %d (%s) finished: status=%s duration=%.1fs',
            task.id, task.name, log_entry.status, log_entry.duration_secs,
        )


def _cleanup_old_logs():
    with _app.app_context():
        from app.models import ExecutionLog, db

        days = _app.config.get('LOG_RETENTION_DAYS', 30)
        cutoff = datetime.now() - timedelta(days=days)
        deleted = ExecutionLog.query.filter(ExecutionLog.started_at < cutoff).delete()
        db.session.commit()
        if deleted:
            logger.info('Log retention: deleted %d logs older than %s', deleted, cutoff)
