from flask import Blueprint, render_template, request

from app.auth import login_required
from app.models import ExecutionLog, Task

bp = Blueprint('logs', __name__)

PER_PAGE = 30


@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    task_id = request.args.get('task_id', type=int)
    status = request.args.get('status', '')

    query = ExecutionLog.query.order_by(ExecutionLog.started_at.desc())

    if task_id:
        query = query.filter_by(task_id=task_id)
    if status:
        query = query.filter_by(status=status)

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    tasks = Task.query.order_by(Task.name).all()

    return render_template(
        'logs.html',
        logs=pagination.items,
        pagination=pagination,
        tasks=tasks,
        filter_task_id=task_id,
        filter_status=status,
    )


@bp.route('/<int:log_id>')
@login_required
def detail(log_id):
    log = ExecutionLog.query.get_or_404(log_id)
    return render_template('log_detail.html', log=log)
