from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, default='')
    cron_expr = db.Column(db.String(100), nullable=False)
    command = db.Column(db.Text, nullable=False)
    working_dir = db.Column(db.String(500), default=None)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    timeout_secs = db.Column(db.Integer, default=3600)
    last_run_at = db.Column(db.DateTime, nullable=True)
    last_run_status = db.Column(db.String(20), nullable=True)
    last_run_duration_secs = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    logs = db.relationship(
        'ExecutionLog', backref='task', lazy='dynamic',
        order_by='ExecutionLog.started_at.desc()',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<Task {self.id}: {self.name}>'


class ExecutionLog(db.Model):
    __tablename__ = 'execution_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(
        db.Integer,
        db.ForeignKey('tasks.id', ondelete='CASCADE'),
        nullable=False,
    )
    trigger_type = db.Column(db.String(20), default='scheduled')
    started_at = db.Column(db.DateTime, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    duration_secs = db.Column(db.Float, nullable=True)
    exit_code = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='running')
    stdout = db.Column(db.Text, default='')
    stderr = db.Column(db.Text, default='')

    def __repr__(self):
        return f'<ExecutionLog {self.id}: task={self.task_id} status={self.status}>'
