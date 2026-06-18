from django.apps import AppConfig


class NewsConfig(AppConfig):
    """App configuration for the news application."""

    name = 'news'

    def ready(self):
        """Connect signal handlers when the app registry is fully populated."""
        import news.signals  # noqa: F401
