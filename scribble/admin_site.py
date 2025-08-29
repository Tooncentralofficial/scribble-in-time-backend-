from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from .views import AdminDashboardView

class CustomAdminSite(admin.AdminSite):
    site_header = 'Scribble in Time Administration'
    site_title = 'Scribble in Time Admin'
    index_title = _('Dashboard')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(AdminDashboardView.as_view()), name='admin_dashboard'),
        ]
        return custom_urls + urls

# Create an instance of our custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')
