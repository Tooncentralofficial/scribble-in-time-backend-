from django.urls import path
from django.views.generic import TemplateView
from .views import chat, upload_document, chat_page

urlpatterns = [
    # Chat endpoints
    path('chat/', chat, name='chat'),
    path('chat-page/', chat_page, name='chat_page'),
    path('upload/', upload_document, name='upload_document'),
    
    # Admin Dashboard
    path('admin/dashboard/', login_required(AdminDashboardView.as_view()), name='admin_dashboard'),
    
    # API Endpoints
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('api/conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('api/conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('api/conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message_list'),
    path('api/conversations/<int:pk>/toggle-ai/', ToggleAIResponseView.as_view(), name='toggle_ai'),
    path('api/conversations/<int:conversation_id>/mark-read/', MarkMessagesAsReadView.as_view(), name='mark_messages_read'),
    path('api/documents/', DocumentListView.as_view(), name='document_list'),
    path('api/documents/<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    
    # Django Admin (optional, can be removed if not needed)
    path('django-admin/', admin.site.urls),
]