import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BestConnect.settings')

app = Celery('BestConnect')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'update-subscription-status': {
        'task': 'subscriptions.tasks.update_subscription_status',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'generate-daily-statistics': {
        'task': 'subscriptions.tasks.generate_daily_statistics',
        'schedule': crontab(hour=0, minute=0),  # À minuit chaque jour
    },
    'check-connectivity': {
        'task': 'subscriptions.tasks.check_connectivity',
        'schedule': crontab(minute='*/1'),  # Toutes les minutes
    },
} 