from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('features/', views.FeaturesView.as_view(), name='features'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('offline/', views.OfflineView.as_view(), name='offline'),
]