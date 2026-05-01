from celery import Celery
from celery.schedules import crontab
from .celery_app import celery

# Scheduled tasks
celery.conf.beat_schedule = {
    'evaluate-alerts-every-5-minutes': {
        'task': 'backend.app.tasks.workers.evaluate_alerts',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-sales-drop-daily': {
        'task': 'backend.app.tasks.workers.check_sales_drop_alerts',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'check-anomalies-hourly': {
        'task': 'backend.app.tasks.workers.check_anomaly_alerts',
        'schedule': crontab(minute=0),  # Every hour
    },
}

celery.conf.beat_schedule_filename = 'celerybeat-schedule'