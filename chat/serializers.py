from rest_framework import serializers
from .models import Message, KnowledgeDocument

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'sender_username', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'file', 'file_type', 
            'is_processed', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_processed', 'processing_error',
            'created_at', 'updated_at'
        ]
