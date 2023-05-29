"""
    Application definition & config settings for smartserve app.
"""

from django.apps import AppConfig


class SmartServeConfig(AppConfig):
    """ Config class to hold application's definition & configuration settings. """

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "smartserve"
    verbose_name: str = "SmartServe"
