from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from .views import chat
from . import admin_views
from .api_views import DocumentDeleteView

router = DefaultRouter()
router.register(r'conversations', api_views.ConversationViewSet)
router.register(r'messages', api_views.MessageViewSet)
router.register(r'documents', api_views.DocumentViewSet)

admin_router = DefaultRouter()
admin_router.register(r'admin/conversations', admin_views.AdminConversationViewSet, basename='admin-conversation')
admin_router.register(r'admin/messages', admin_views.AdminMessageViewSet, basename='admin-message')
admin_router.register(r'admin/search', admin_views.AdminSearchViewSet, basename='admin-search')

urlpatterns = [
    # Admin dashboard stats
    path('dashboard/stats/', api_views.DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Toggle AI responses
    path('conversations/<int:pk>/toggle-ai/', api_views.ToggleAIResponseView.as_view(), name='toggle-ai'),
    
    # Admin reply to conversation
    path('conversations/<int:conversation_id>/reply/', api_views.AdminReplyView.as_view(), name='admin-reply'),
    
    # Document upload
    path('documents/upload/', api_views.DocumentUploadView.as_view(), name='document-upload'),
    
    # User management
    path('users/', api_views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', api_views.UserDetailView.as_view(), name='user-detail'),
    
    # Settings
    path('settings/', api_views.AdminSettingsView.as_view(), name='admin-settings'),
    
    # Chat endpoint
    path('chat/', chat, name='chat'),
    
    # Document management
    path('documents/delete/', DocumentDeleteView.as_view(), name='delete-document'),
]

# Include router URLs
urlpatterns += router.urls

# Include admin router URLs without the 'admin/' prefix to avoid duplication
urlpatterns += admin_router.urls
