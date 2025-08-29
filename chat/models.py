from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Conversation(models.Model):
    """Represents a conversation between users and the system"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ]
    
    user_id = models.CharField(max_length=255, db_index=True)  # Can be user ID or session ID
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['user_id']
    
    def __str__(self):
        return f"Conversation {self.id} - User: {self.user_id}"


class KnowledgeDocument(models.Model):
    """Stores information about documents used for AI knowledge base"""
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('txt', 'Text'),
        ('md', 'Markdown'),
        ('docx', 'Word Document'),
    ]
    
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='knowledge_docs/')
    file_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_file_type_display()})"


class Message(models.Model):
    """Represents a message in a conversation"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Assistant'),
        ('admin', 'Admin')
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField(validators=[MinLengthValidator(1)])
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender_username = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:50]}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    @classmethod
    def get_conversation_messages(cls, user_id):
        """Get all messages for a user's conversation"""
        try:
            conversation = Conversation.objects.get(user_id=user_id)
            return cls.objects.filter(conversation=conversation)
        except Conversation.DoesNotExist:
            return cls.objects.none()
