from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.persistence"
    verbose_name = "Infrastructure Persistence"
