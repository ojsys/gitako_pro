from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    
    def ready(self):
        """
        Override admin site for custom dashboard
        """
        from django.contrib import admin
        from .admin_context import admin_dashboard_context
        
        # Store original index method
        original_index = admin.site.index
        
        def custom_index(request, extra_context=None):
            """Add dashboard statistics to admin index"""
            extra_context = extra_context or {}
            extra_context.update(admin_dashboard_context(request))
            return original_index(request, extra_context)
        
        # Replace admin index with custom version
        admin.site.index = custom_index