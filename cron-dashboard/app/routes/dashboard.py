from datetime import datetime

from croniter import croniter
from cron_descriptor import get_description
from flask import Blueprint, render_template

from app.auth import login_required, login_view, logout_view
from app.models import Task

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    tasks = Task.query.order_by(Task.id).all()
    task_data = []
    for task in tasks:
        next_run = None
        human_cron = ''
        if task.enabled:
            try:
                cron = croniter(task.cron_expr, datetime.now())
                next_run = cron.get_next(datetime)
                human_cron = get_description(task.cron_expr)
            except (ValueError, KeyError):
                human_cron = 'Invalid expression'
        task_data.append({
            'task': task,
            'next_run': next_run,
            'human_cron': human_cron,
        })
    return render_template('dashboard.html', task_data=task_data)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    return login_view()


@bp.route('/logout')
def logout():
    return logout_view()
