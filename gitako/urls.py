"""
URL configuration for gitako project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.cms.urls')),  # Public pages
    path('auth/', include('apps.accounts.urls')),  # Authentication
    path('dashboard/', include('apps.api.urls', namespace='dashboard')),  # Dashboard and main app
    path('farms/', include('apps.farms.urls')),
    path('calendar/', include('apps.calendar.urls')),
    path('budget/', include('apps.budget.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('marketplace/', include('apps.marketplace.urls')),  # Re-enabled after fixing encoding issue
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files in production for cPanel hosting
# This is necessary because cPanel shared hosting doesn't have a web server 
# configuration to serve media files directly
else:
    # Only serve media files in production, static files are handled by WhiteNoise
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
