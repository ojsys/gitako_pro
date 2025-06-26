from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard and main views
    path('', views.reports_dashboard, name='dashboard'),
    path('list/', views.report_list, name='report_list'),
    path('create/', views.create_report, name='create_report'),
    path('<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('<uuid:report_id>/regenerate/', views.regenerate_report, name='regenerate_report'),
    path('<uuid:report_id>/delete/', views.delete_report, name='delete_report'),
    
    # Export functionality
    path('<uuid:report_id>/export/', views.export_report, name='export_report'),
    path('export/<uuid:export_id>/download/', views.download_export, name='download_export'),
    
    # Specialized report views
    path('financial/', views.financial_reports, name='financial_reports'),
    path('production/', views.production_reports, name='production_reports'),
    path('executive/', views.executive_dashboard, name='executive_dashboard'),
    
    # API endpoints
    path('api/<uuid:report_id>/data/', views.report_api_data, name='report_api_data'),
    
    # Scheduling
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.create_schedule, name='create_schedule'),
]