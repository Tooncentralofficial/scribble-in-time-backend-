from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Document, AdminSettings

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
        read_only_fields = ['date_joined']

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'sender', 'conversation']
        read_only_fields = ['sender']
        extra_kwargs = {
            'conversation': {'required': False}
        }

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'content', 'sender', 'sender_name', 'created_at', 'is_read']
        read_only_fields = ['created_at', 'is_read']
    
    def get_sender_name(self, obj):
        if obj.sender == 'user':
            if obj.conversation and obj.conversation.user:
                return obj.conversation.user.email
            return 'Unknown User'
        return obj.sender.upper()

class ConversationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'user', 'user_email', 'created_at', 'updated_at', 'is_active', 'ai_enabled', 'last_message', 'unread_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'content': last_message.content[:100] + ('...' if len(last_message.content) > 100 else ''),
                'sender': last_message.sender,
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        return obj.messages.filter(is_read=False, sender='user').count()

class ConversationListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'is_active', 'ai_enabled', 'last_message', 'unread_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'sender': last_message.sender,
                'created_at': last_message.created_at
            }
        return None

    def get_unread_count(self, obj):
        return obj.messages.filter(is_read=False).exclude(sender='user').count()

class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'is_active', 'ai_enabled', 'messages']
        read_only_fields = ['created_at', 'updated_at']

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'document_type', 'file', 'file_url', 'file_size', 'uploaded_by', 'uploaded_at', 'is_active']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_url', 'file_size']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return 0

class AdminSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSettings
        fields = ['ai_enabled', 'auto_response', 'response_timeout', 'updated_at']
        read_only_fields = ['updated_at']

# Alias for backward compatibility
ConversationDetail = ConversationDetailSerializer
