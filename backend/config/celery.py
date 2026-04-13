import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    # Fee payment reminders - run daily at 9 AM
    'fee-payment-reminders': {
        'task': 'admissions.tasks.send_fee_payment_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Overdue fee notifications - run daily at 10 AM
    'overdue-fee-notifications': {
        'task': 'admissions.tasks.send_overdue_fee_notifications',
        'schedule': crontab(hour=10, minute=0),
    },
    # You can add more periodic tasks here
    # 'example-task': {
    #     'task': 'app.tasks.example_task',
    #     'schedule': crontab(minute='*/15'),  # Every 15 minutes
    # },
}

app.conf.timezone = 'UTC'