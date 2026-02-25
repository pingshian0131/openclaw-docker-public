from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import login_required
from app.models import Task, db
from app.scheduler import add_job, remove_job

bp = Blueprint('tasks', __name__)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        cron_expr = request.form.get('cron_expr', '').strip()
        command = request.form.get('command', '').strip()
        description = request.form.get('description', '').strip()
        working_dir = request.form.get('working_dir', '').strip() or None
        timeout_secs = int(request.form.get('timeout_secs', '3600'))
        enabled = 'enabled' in request.form

        if not name or not cron_expr or not command:
            flash('Name, cron expression, and command are required.', 'danger')
            return render_template('task_form.html', mode='create', form=request.form)

        if Task.query.filter_by(name=name).first():
            flash(f'Task name "{name}" already exists.', 'danger')
            return render_template('task_form.html', mode='create', form=request.form)

        task = Task(
            name=name, cron_expr=cron_expr, command=command,
            description=description, working_dir=working_dir,
            timeout_secs=timeout_secs, enabled=enabled,
        )
        db.session.add(task)
        db.session.commit()

        if task.enabled:
            add_job(task)

        flash(f'Task "{name}" created.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('task_form.html', mode='create', form={})


@bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.name = request.form.get('name', '').strip()
        task.cron_expr = request.form.get('cron_expr', '').strip()
        task.command = request.form.get('command', '').strip()
        task.description = request.form.get('description', '').strip()
        task.working_dir = request.form.get('working_dir', '').strip() or None
        task.timeout_secs = int(request.form.get('timeout_secs', '3600'))
        task.enabled = 'enabled' in request.form

        if not task.name or not task.cron_expr or not task.command:
            flash('Name, cron expression, and command are required.', 'danger')
            return render_template('task_form.html', mode='edit', task=task, form=request.form)

        db.session.commit()

        remove_job(task.id)
        if task.enabled:
            add_job(task)

        flash(f'Task "{task.name}" updated.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('task_form.html', mode='edit', task=task, form={})


@bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    name = task.name
    remove_job(task.id)
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{name}" deleted.', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    recent_logs = task.logs.limit(20).all()
    return render_template('task_detail.html', task=task, logs=recent_logs)
