"""
Celery configuration for JobTrack Automate.

Sets up the Celery app so we can run background tasks
like automated applications and sending reminders.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('jobtrack')

# Pull config from Django settings, using the CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Pick up all task modules from installed apps
app.autodiscover_tasks()

# Scheduled tasks that run at set times
app.conf.beat_schedule = {
    # Check for reminders every morning at 8am
    'check-reminders-daily': {
        'task': 'tasks.automation_tasks.check_and_send_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Run automated job searches at 9am on weekdays
    'automated-job-search': {
        'task': 'tasks.automation_tasks.run_automated_searches',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),
    },
    # Clean up old screenshots every Sunday at midnight
    'cleanup-screenshots': {
        'task': 'tasks.automation_tasks.cleanup_old_screenshots',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),
    },
}
