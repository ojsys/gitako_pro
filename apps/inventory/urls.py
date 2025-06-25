from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('supplies/', views.SupplyListView.as_view(), name='supplies'),
]