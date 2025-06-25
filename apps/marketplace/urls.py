from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.MarketplaceListView.as_view(), name='list'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('product/create/', views.ProductCreateView.as_view(), name='create_product'),
    path('product/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='edit_product'),
    path('product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete_product'),
    path('product/<int:pk>/update-status/', views.ProductStatusUpdateView.as_view(), name='update_product_status'),
    path('product/<int:pk>/duplicate/', views.ProductDuplicateView.as_view(), name='duplicate_product'),
    path('product/<int:product_pk>/inquire/', views.InquiryCreateView.as_view(), name='create_inquiry'),
    path('my-products/', views.MyProductsView.as_view(), name='my_products'),
    path('my-inquiries/', views.MyInquiriesView.as_view(), name='my_inquiries'),
    path('transactions/', views.TransactionListView.as_view(), name='transactions'),
]