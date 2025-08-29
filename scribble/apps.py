from django.apps import AppConfig
from django.conf import settings


class ScribbleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scribble'
    verbose_name = 'Scribble AI'
    
    def ready(self):
        # Make sure the AUTH_USER_MODEL is set
        if not hasattr(settings, 'AUTH_USER_MODEL'):
            settings.AUTH_USER_MODEL = 'scribble.User'
            
        # Import signals after the app is ready
        try:
            import scribble.signals  # noqa F401
        except ImportError:
            # Don't fail if signals can't be imported
            pass
