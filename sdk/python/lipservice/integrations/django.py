"""Django integration for LipService SDK."""

from typing import Any

try:
    from django.conf import settings
except ImportError:
    raise ImportError("Django is not installed. Install with: pip install lipservice-sdk[django]")

from lipservice.config import configure_adaptive_logging


def configure_lipservice_django() -> None:
    """
    Configure LipService for Django applications.

    Add this to your Django settings:

        LIPSERVICE = {
            'SERVICE_NAME': 'my-django-app',
            'LIPSERVICE_URL': 'https://lipservice.company.com',
            'API_KEY': 'optional-api-key',
        }

    Then call this function in your AppConfig.ready() method:

        class MyAppConfig(AppConfig):
            def ready(self):
                from lipservice.integrations.django import configure_lipservice_django
                configure_lipservice_django()
    """
    if not hasattr(settings, "LIPSERVICE"):
        raise ValueError("LIPSERVICE settings not found in Django settings")

    lipservice_settings: dict[str, Any] = settings.LIPSERVICE

    configure_adaptive_logging(
        service_name=lipservice_settings["SERVICE_NAME"],
        lipservice_url=lipservice_settings["LIPSERVICE_URL"],
        api_key=lipservice_settings.get("API_KEY"),
        policy_refresh_interval=lipservice_settings.get("POLICY_REFRESH_INTERVAL", 300),
        pattern_report_interval=lipservice_settings.get("PATTERN_REPORT_INTERVAL", 600),
    )


class LipServiceDjangoHandler:
    """
    Django logging handler configuration.

    Add this to your Django LOGGING configuration:

        LOGGING = {
            'handlers': {
                'lipservice': {
                    'class': 'lipservice.integrations.django.LipServiceDjangoHandler',
                    'level': 'INFO',
                },
            },
            'loggers': {
                'django': {
                    'handlers': ['lipservice'],
                    'level': 'INFO',
                },
            },
        }
    """

    pass  # Placeholder for Django handler class

