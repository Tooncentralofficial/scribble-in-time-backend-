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
    actions = ['reprocess_documents']
    
    def get_list_display(self, request):
        """Dynamically add processing_error to list_display if field exists"""
        list_display = list(super().get_list_display(request))
        try:
            # Check if processing_error field exists
            from .models import KnowledgeDocument
            if hasattr(KnowledgeDocument, 'processing_error'):
                if 'processing_error' not in list_display:
                    list_display.append('processing_error')
        except:
            pass
        return list_display
    
    def get_readonly_fields(self, request, obj=None):
        """Dynamically add processing_error to readonly_fields if field exists"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        try:
            # Check if processing_error field exists
            from .models import KnowledgeDocument
            if hasattr(KnowledgeDocument, 'processing_error'):
                if 'processing_error' not in readonly_fields:
                    readonly_fields.append('processing_error')
        except:
            pass
        return readonly_fields
    
    def reprocess_documents(self, request, queryset):
        """Reprocess selected documents"""
        from .ingest import main
        
        success_count = 0
        for doc in queryset:
            try:
                # Reset processing status
                doc.is_processed = False
                doc.processing_error = None
                doc.save()
                
                # Reprocess
                if main():
                    doc.is_processed = True
                    doc.save()
                    success_count += 1
                else:
                    doc.processing_error = "Reprocessing failed"
                    doc.save()
            except Exception as e:
                doc.processing_error = str(e)
                doc.save()
        
        if success_count > 0:
            self.message_user(request, f"Successfully reprocessed {success_count} documents.", level='success')
        else:
            self.message_user(request, "Failed to reprocess documents. Check processing errors.", level='error')
    
    reprocess_documents.short_description = "Reprocess selected documents"
    
    def save_model(self, request, obj, *args, **kwargs):
        from .ingest import load_documents, chunk_documents, create_or_update_vector_store
        from pathlib import Path
        import os
        import shutil
        
        # Save the document first
        super().save_model(request, obj, *args, **kwargs)
        
        # Process the document
        try:
            # Get the correct knowledge base directory
            project_root = Path(__file__).resolve().parent.parent
            docs_dir = project_root / "knowledge_base"
            os.makedirs(docs_dir, exist_ok=True)
            
            # Copy the uploaded file to the knowledge base directory
            source_path = obj.file.path
            filename = os.path.basename(obj.file.name)
            dest_path = docs_dir / filename
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            # Process the document using the ingest module
            documents = load_documents(str(docs_dir))
            if documents:
                chunks = chunk_documents(documents)
                vector_store = create_or_update_vector_store(chunks)
                
                if vector_store:
                    # Mark as processed
                    obj.is_processed = True
                    # Don't trigger save_model again to avoid recursion
                    KnowledgeDocument.objects.filter(pk=obj.pk).update(is_processed=True)
                    
                    # Update cache to indicate documents are available
                    from django.core.cache import cache
                    cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
                    
                    self.message_user(request, f"Document '{filename}' processed successfully and added to knowledge base!", level='success')
                else:
                    raise Exception("Failed to create vector store")
            else:
                raise Exception("No documents were loaded from the file")
                
        except Exception as e:
            self.message_user(request, f"Error processing document: {str(e)}", level='error')
            # Mark as not processed
            obj.is_processed = False
            
            # Only set processing_error if the field exists
            try:
                if hasattr(obj, 'processing_error'):
                    obj.processing_error = str(e)
                    KnowledgeDocument.objects.filter(pk=obj.pk).update(
                        is_processed=False, 
                        processing_error=str(e)
                    )
                else:
                    KnowledgeDocument.objects.filter(pk=obj.pk).update(is_processed=False)
            except:
                # Fallback if processing_error field doesn't exist
                KnowledgeDocument.objects.filter(pk=obj.pk).update(is_processed=False)

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
