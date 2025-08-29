from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, AdminSettings

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Create default admin settings when a new superuser is created"""
    if created and instance.is_superuser:
        AdminSettings.objects.get_or_create(
            user=instance,
            defaults={
                'ai_enabled': True,
                'auto_response': True,
                'response_timeout': 30,
            }
        )
