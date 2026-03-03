# blog_core/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_core.settings')

app = Celery('blog_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule news updates
app.conf.beat_schedule = {
    'fetch-news-every-hour': {
        'task': 'blog.tasks.fetch_latest_news',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'generate-ai-posts': {
        'task': 'blog.tasks.generate_ai_posts',
        'schedule': crontab(minute=30, hour='*/3'),  # Every 3 hours
    },
}