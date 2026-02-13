"""
Apps configuration for the applications app.
"""
from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications'
    verbose_name = 'Job Applications'

    def ready(self) -> None:
        """Hook up signals when the app loads."""
        import applications.signals  # noqa: F401
