# This file is kept for backward compatibility
# All models have been moved to models.py

from django.db import models

class AdminSettings(models.Model):
    ai_enabled = models.BooleanField(default=True)
    auto_response = models.BooleanField(default=True)
    response_timeout = models.PositiveIntegerField(default=60, help_text="Response timeout in seconds")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Admin Settings"
        
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
