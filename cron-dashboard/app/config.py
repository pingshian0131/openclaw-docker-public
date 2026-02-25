import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    SQLALCHEMY_DATABASE_URI = 'sqlite:////data/cron_dashboard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'changeme')
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', '30'))
    MAX_LOG_OUTPUT_BYTES = int(os.environ.get('MAX_LOG_OUTPUT_BYTES', '524288'))
    TZ = os.environ.get('TZ', 'Asia/Taipei')
