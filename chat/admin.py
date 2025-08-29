from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('content', 'sender', 'sender_username', 'is_read', 'created_at')
    ordering = ('-created_at',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('id', 'user_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [MessageInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def has_add_permission(self, request):
        return False  # Prevent adding conversations directly from admin

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_id', 'content_preview', 'sender', 'is_read', 'created_at')
    list_filter = ('sender', 'is_read', 'created_at')
    search_fields = ('content', 'sender_username', 'conversation__user_id')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('conversation',)
    
    def get_user_id(self, obj):
        return obj.conversation.user_id
    get_user_id.short_description = 'User ID'
    get_user_id.admin_order_field = 'conversation__user_id'
    
    @admin.display(description='Message')
    def content_preview(self, obj):
        return f"{obj.content[:50]}..." if len(obj.content) > 50 else obj.content
