from django.urls import path
from . import views

app_name = 'farms'

urlpatterns = [
    path('', views.FarmListView.as_view(), name='list'),
    path('create/', views.FarmCreateView.as_view(), name='create'),
    path('<int:pk>/', views.FarmDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.FarmUpdateView.as_view(), name='update'),
    path('blocks/', views.BlockListView.as_view(), name='blocks'),
    path('blocks/create/', views.BlockCreateView.as_view(), name='block_create'),
    path('blocks/<int:pk>/', views.BlockDetailView.as_view(), name='block_detail'),
    path('blocks/<int:pk>/edit/', views.BlockUpdateView.as_view(), name='block_update'),
    path('staff/', views.StaffListView.as_view(), name='staff'),
    path('staff/create/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('farmers/', views.FarmerListView.as_view(), name='farmers'),
    path('farmers/create/', views.FarmerCreateView.as_view(), name='farmer_create'),
    path('farmers/<int:pk>/', views.FarmerDetailView.as_view(), name='farmer_detail'),
    path('farmers/<int:pk>/edit/', views.FarmerUpdateView.as_view(), name='farmer_update'),
    path('farmers/bulk-upload/', views.FarmerBulkUploadView.as_view(), name='farmer_bulk_upload'),
    path('farmers/upload-template/', views.FarmerUploadTemplateView.as_view(), name='farmer_upload_template'),
]