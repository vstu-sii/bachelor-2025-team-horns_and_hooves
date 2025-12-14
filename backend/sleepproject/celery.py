import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sleepproject.settings')

app = Celery('sleepproject')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_reminder_email': {
        'task': 'sleep_tracking_app.tasks.send_reminder_email',
        'schedule': crontab(minute=0, hour=20),  # Один раз в день
    },

}

app.conf.broker_connection_retry_on_startup = True
