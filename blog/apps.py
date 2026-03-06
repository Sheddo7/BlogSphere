# blog/apps.py
import sys
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        # Don't start scheduler during management commands
        skip = ['migrate', 'makemigrations', 'collectstatic',
                 'shell', 'createsuperuser', 'test', 'check', 'dbshell']
        if any(cmd in sys.argv for cmd in skip):
            return
        try:
            from blog import scheduler
            scheduler.start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Scheduler not started: {e}")