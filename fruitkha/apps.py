from django.apps import AppConfig

class FruitkhaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fruitkha'

    def ready(self):
        from . import signals  # Load signal handlers