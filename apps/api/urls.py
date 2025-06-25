from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
    
    # API endpoints for dynamic forms
    path('api/farms/<int:farm_id>/blocks/', views.FarmBlocksAPIView.as_view(), name='farm_blocks_api'),
    path('api/crops/<int:crop_id>/varieties/', views.CropVarietiesAPIView.as_view(), name='crop_varieties_api'),
]