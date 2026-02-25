from datetime import datetime

from croniter import croniter
from cron_descriptor import get_description
from flask import Blueprint, jsonify, request

from app.auth import login_required
from app.models import Task, db
from app.scheduler import add_job, remove_job, run_now

bp = Blueprint('api', __name__)


@bp.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.enabled = not task.enabled
    db.session.commit()

    if task.enabled:
        add_job(task)
    else:
        remove_job(task.id)

    return jsonify({'enabled': task.enabled, 'id': task.id})


@bp.route('/tasks/<int:task_id>/run', methods=['POST'])
@login_required
def run_task(task_id):
    task = Task.query.get_or_404(task_id)
    run_now(task.id)
    return jsonify({'status': 'started', 'id': task.id})


@bp.route('/cron/validate', methods=['POST'])
@login_required
def validate_cron():
    data = request.get_json(silent=True) or {}
    expression = data.get('expression', '').strip()

    if not expression:
        return jsonify({'valid': False, 'error': 'Expression is empty'})

    try:
        cron = croniter(expression, datetime.now())
        next_runs = [cron.get_next(datetime).strftime('%Y-%m-%d %H:%M') for _ in range(3)]
        description = get_description(expression)
        return jsonify({
            'valid': True,
            'description': description,
            'next_runs': next_runs,
        })
    except (ValueError, KeyError) as e:
        return jsonify({'valid': False, 'error': str(e)})
