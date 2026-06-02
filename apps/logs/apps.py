from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.logs"
    verbose_name = "Logs de auditoria"

    def ready(self):
        import apps.logs.signals  # noqa: F401
