from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Conversation,
    Message,
    Document,
    AdminSettings,
    KnowledgeDocument
)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('content', 'sender', 'is_read', 'created_at')
    show_change_link = True

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'is_active', 'ai_enabled')
    list_filter = ('is_active', 'ai_enabled', 'created_at')
    search_fields = ('user__email', 'user__username')
    inlines = [MessageInline]
    list_select_related = ('user',)
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_email', 'sender', 'is_read', 'created_at')
    list_filter = ('sender', 'is_read', 'created_at')
    search_fields = ('content', 'conversation__user__email')
    list_select_related = ('conversation__user',)
    date_hierarchy = 'created_at'
    
    def get_user_email(self, obj):
        return obj.conversation.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'conversation__user__email'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'uploaded_by', 'uploaded_at', 'is_active')
    list_filter = ('document_type', 'is_active', 'uploaded_at')
    search_fields = ('title', 'document_type')
    readonly_fields = ('uploaded_by', 'uploaded_at')
    list_select_related = ('uploaded_by',)
    date_hierarchy = 'uploaded_at'

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set the uploaded_by field if this is a new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'ai_enabled', 'auto_response', 'response_timeout', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('updated_at',)
    list_select_related = ('user',)

    def has_add_permission(self, request):
        # Only allow one settings object per user
        return not AdminSettings.objects.exists()

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at', 'is_processed')
    readonly_fields = ('uploaded_at', 'is_processed')
    date_hierarchy = 'uploaded_at'
    
    def save_model(self, request, obj, *args, **kwargs):
        from .ingest import load_documents, chunk_documents, create_or_update_vector_store
        from pathlib import Path
        import os
        
        # Save the document first
        super().save_model(request, obj, *args, **kwargs)
        
        # Process the document
        try:
            # Load and process the document
            docs_dir = os.path.join('media', 'knowledge_base')
            os.makedirs(docs_dir, exist_ok=True)
            
            # Save the file to the knowledge base directory
            file_path = os.path.join(docs_dir, os.path.basename(obj.file.name))
            with open(file_path, 'wb+') as destination:
                for chunk in obj.file.chunks():
                    destination.write(chunk)
            
            # Process the document
            documents = load_documents(docs_dir)
            if documents:
                chunks = chunk_documents(documents)
                create_or_update_vector_store(chunks)
                obj.is_processed = True
                # Don't trigger save_model again to avoid recursion
                KnowledgeDocument.objects.filter(pk=obj.pk).update(is_processed=True)
                
                # Update the DOCUMENTS_UPLOADED setting
                from django.conf import settings
                if not hasattr(settings, 'DOCUMENTS_UPLOADED') or not settings.DOCUMENTS_UPLOADED:
                    from django.conf import settings as django_settings
                    setattr(django_settings, 'DOCUMENTS_UPLOADED', True)
                
        except Exception as e:
            self.message_user(request, f"Error processing document: {str(e)}", level='error')

# Custom User Admin
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_admin', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions')
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')},
        ),
    )

# Register the custom User model with our UserAdmin
admin.site.register(User, UserAdmin)
