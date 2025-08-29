"""
URL configuration for scribbleintimeai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

urlpatterns = [
    # API endpoints
    path('api/', include('scribble.api_urls')),
    
    # Chat endpoints - handle with/without trailing slash
    path('api/chat/', include('chat.urls')),
    
    # Authentication
    path('api/auth/', include('rest_framework.urls')),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Frontend (served by Django in development)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
