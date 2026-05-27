from django.apps import AppConfig


class PersonnelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.personnel"
    verbose_name = "Personnel"

    def ready(self) -> None:  # pragma: no cover
        from . import signals  # noqa: F401

        return super().ready()
