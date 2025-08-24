from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='list'),
    path('create/', views.BudgetCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='detail'),
    path('<int:pk>/enhanced-summary/', views.EnhancedBudgetSummaryView.as_view(), name='enhanced_summary'),
    path('<int:budget_id>/add-item/', views.BudgetItemCreateView.as_view(), name='add_item'),
    path('<int:budget_id>/add-income/', views.BudgetIncomeItemCreateView.as_view(), name='add_income'),
    path('<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='edit'),
    
    # AJAX endpoints for dynamic field population
    path('ajax/load-blocks/', views.load_blocks, name='ajax_load_blocks'),
    path('ajax/load-calendars/', views.load_calendars, name='ajax_load_calendars'),
    
    # Income item URLs
    path('<int:budget_id>/income/add/', views.IncomeItemCreateView.as_view(), name='income_add'),
    path('income/<int:pk>/edit/', views.IncomeItemUpdateView.as_view(), name='income_edit'),
    path('income/<int:pk>/delete/', views.IncomeItemDeleteView.as_view(), name='income_delete'),
    
    # Expense item URLs
    path('<int:budget_id>/expense/add/', views.ExpenseItemCreateView.as_view(), name='expense_add'),
    path('expense/<int:pk>/edit/', views.ExpenseItemUpdateView.as_view(), name='expense_edit'),
    path('expense/<int:pk>/delete/', views.ExpenseItemDeleteView.as_view(), name='expense_delete'),
]