"""
    Application definition & config settings for smartserve app.
"""

from django.apps import AppConfig


class SmartServeConfig(AppConfig):
    """ Config class to hold application's definition & configuration settings. """

    default_auto_field = "django.db.models.BigAutoField"
    name = "smartserve"
    verbose_name = "SmartServe"

    @staticmethod
    def ready(**kwargs) -> None:
        """
            Import function that ensures the signal handlers within this app
            are loaded and waiting for signals to be sent.
        """

        from smartserve.models import signals
        signals.ready()
