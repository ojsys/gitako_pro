from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    # Calendar URLs
    path('', views.CalendarListView.as_view(), name='list'),
    path('create/', views.CalendarCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CalendarDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CalendarUpdateView.as_view(), name='edit'),
    
    # Activity URLs
    path('activities/', views.ActivityListView.as_view(), name='activities'),
    path('activities/create/', views.ActivityCreateView.as_view(), name='activity_create'),
    path('activities/<int:pk>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('activities/<int:pk>/edit/', views.ActivityUpdateView.as_view(), name='activity_edit'),
    path('activities/<int:pk>/delete/', views.ActivityDeleteView.as_view(), name='activity_delete'),
    path('activities/<int:pk>/start/', views.activity_start, name='activity_start'),
    path('activities/<int:pk>/complete/', views.activity_complete, name='activity_complete'),
]