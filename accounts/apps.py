from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """App configuration for the accounts application."""

    name = 'accounts'

    def ready(self):
        """Connect signal handlers when the app registry is fully populated."""
        import accounts.signals  # noqa: F401
