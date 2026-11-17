from django.apps import AppConfig


class RealtyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realty'

    def ready(self):
        from realty import signals  # noqa: F401
