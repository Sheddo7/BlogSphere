# blog/apps.py
from django.apps import AppConfig
import sys


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        """Start the scheduler when Django starts (but not during migrations/tests)."""
        # Don't run scheduler during manage.py commands like migrate, collectstatic
        is_manage_command = any(
            cmd in sys.argv for cmd in [
                'migrate', 'makemigrations', 'collectstatic',
                'shell', 'createsuperuser', 'test', 'check'
            ]
        )
        if not is_manage_command:
            try:
                from blog import scheduler
                scheduler.start()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Scheduler failed to start: {e}")