from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Sum, Count, Q, Avg, F, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from apps.farms.models import Farm, Block, Crop, CropVariety, FarmStaff, FarmerRecord
from apps.farms.mixins import FarmAccessMixin
from apps.farms.permissions import RolePermissionMixin


class DashboardView(LoginRequiredMixin, RolePermissionMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's accessible farms based on role
        if user.is_superuser or user.role == 'admin':
            user_farms = Farm.objects.filter(is_active=True)
        elif user.role == 'farm_owner':
            user_farms = Farm.objects.filter(owner=user, is_active=True)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Get farms where user is owner or staff member
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            # Combine both querysets
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            user_farms = Farm.objects.filter(id__in=farm_ids, is_active=True).distinct()
        else:
            user_farms = Farm.objects.none()
        
        # Basic Farm Analytics
        context['total_farms'] = user_farms.count()
        context['total_area'] = user_farms.aggregate(total=Sum('total_area'))['total'] or 0
        
        # Block Analytics
        user_blocks = Block.objects.filter(farm__in=user_farms, is_active=True)
        context['total_blocks'] = user_blocks.count()
        context['total_allocated_area'] = user_blocks.aggregate(total=Sum('size'))['total'] or 0
        # Calculate block status based on actual data
        context['growing_blocks'] = user_blocks.filter(
            planting_date__isnull=False,
            actual_harvest_date__isnull=True
        ).count()
        context['harvested_blocks'] = user_blocks.filter(
            actual_harvest_date__isnull=False
        ).count()
        context['pending_blocks'] = user_blocks.filter(
            planting_date__isnull=True
        ).count()
        
        # Crop Distribution Analytics
        crop_distribution = user_blocks.values('crop__name').annotate(
            count=Count('id'),
            total_area=Sum('size')
        ).order_by('-total_area')[:5]
        context['crop_distribution'] = crop_distribution
        
        # Expected vs Actual Yield Analytics
        yield_data = user_blocks.filter(
            expected_yield__isnull=False
        ).aggregate(
            total_expected_yield=Sum('expected_yield'),
            avg_expected_yield=Avg('expected_yield'),
            blocks_with_yield_data=Count('id')
        )
        context['yield_analytics'] = yield_data
        
        # Staff Analytics
        staff_data = FarmStaff.objects.filter(farm__in=user_farms, is_active=True)
        context['total_staff'] = staff_data.count()
        context['staff_by_role'] = staff_data.values('role').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Farmer Records Analytics
        farmer_records = FarmerRecord.objects.filter(farm__in=user_farms, is_active=True)
        context['total_farmers'] = farmer_records.count()
        context['total_farmer_area'] = farmer_records.aggregate(
            total=Sum('allocated_hectares')
        )['total'] or 0
        
        # Calendar/Activities Analytics (if calendar app exists)
        try:
            from apps.calendar.models import CropCalendar, Activity
            
            # Current season calendars
            current_year = timezone.now().year
            current_calendars = CropCalendar.objects.filter(
                farm__in=user_farms,
                season_year=current_year,
                is_active=True
            )
            context['active_calendars'] = current_calendars.count()
            
            # Activities analytics
            user_activities = Activity.objects.filter(
                calendar__farm__in=user_farms
            )
            
            # Recent activities (last 30 days)
            recent_date = timezone.now() - timedelta(days=30)
            context['recent_activities'] = user_activities.filter(
                created_at__gte=recent_date
            ).select_related(
                'calendar', 'calendar__farm', 'assigned_to'
            ).order_by('-created_at')[:5]
            
            # Activity status breakdown
            context['activity_stats'] = {
                'total': user_activities.count(),
                'pending': user_activities.filter(status='pending').count(),
                'in_progress': user_activities.filter(status='in_progress').count(),
                'completed': user_activities.filter(status='completed').count(),
                'overdue': user_activities.filter(
                    status__in=['pending', 'in_progress'],
                    scheduled_date__lt=timezone.now().date()
                ).count()
            }
            
            # Upcoming activities (next 7 days)
            upcoming_date = timezone.now().date() + timedelta(days=7)
            context['upcoming_activities'] = user_activities.filter(
                scheduled_date__lte=upcoming_date,
                scheduled_date__gte=timezone.now().date(),
                status__in=['pending', 'in_progress']
            ).select_related(
                'calendar', 'calendar__farm'
            ).order_by('scheduled_date')[:5]
            
        except ImportError:
            context['active_calendars'] = 0
            context['recent_activities'] = []
            context['activity_stats'] = {
                'total': 0, 'pending': 0, 'in_progress': 0, 'completed': 0, 'overdue': 0
            }
            context['upcoming_activities'] = []
        
        # Budget Analytics (if budget app exists)
        try:
            from apps.budget.models import Budget
            
            user_budgets = Budget.objects.filter(farm__in=user_farms)
            
            # Current season budget summary - include all active budgets and recent ones
            current_season_budgets = user_budgets.filter(
                Q(status='active') | Q(status='draft'),  # Include draft budgets
                start_date__lte=timezone.now().date() + timedelta(days=365),  # More flexible date range
                end_date__gte=timezone.now().date() - timedelta(days=30)   # Include recent past budgets
            )
            
            # Calculate totals from planned income and expenses
            budget_totals = current_season_budgets.aggregate(
                total_planned_income=Sum('total_planned_income'),
                total_planned_expenses=Sum('total_planned_expenses'),
                total_actual_income=Sum('total_actual_income'),
                total_actual_expenses=Sum('total_actual_expenses')
            )
            
            # Calculate meaningful budget summary
            # Use planned income as the total budget (what we expect to make)
            # Use actual expenses as what we've spent
            total_budget_amount = budget_totals['total_planned_income'] or 0
            total_spent_amount = budget_totals['total_actual_expenses'] or 0
            
            # If no planned income, use planned expenses as budget
            if total_budget_amount == 0:
                total_budget_amount = budget_totals['total_planned_expenses'] or 0
            
            context['budget_summary'] = {
                'total_budget': total_budget_amount,
                'total_spent': total_spent_amount, 
                'remaining': total_budget_amount - total_spent_amount,
                'utilization_percentage': round(
                    (total_spent_amount / total_budget_amount * 100) if total_budget_amount > 0 else 0, 1
                )
            }
            
            # Recent expenses - placeholder for future implementation
            context['recent_expenses'] = []
            
        except ImportError:
            context['budget_summary'] = {
                'total_budget': 0, 'total_spent': 0, 'remaining': 0, 'utilization_percentage': 0
            }
            context['recent_expenses'] = []
        
        # Inventory Analytics (if inventory app exists)
        try:
            from apps.inventory.models import Supply, InventoryTransaction
            
            # Low stock alerts
            low_stock_supplies = Supply.objects.filter(
                farm__in=user_farms,
                current_stock__lte=F('minimum_stock'),
                is_active=True
            )
            context['low_stock_count'] = low_stock_supplies.count()
            context['low_stock_supplies'] = low_stock_supplies.select_related('category')[:5]
            
            # Inventory value
            total_inventory_value = Supply.objects.filter(
                farm__in=user_farms,
                is_active=True,
                unit_cost__isnull=False
            ).aggregate(
                total_value=Sum(F('current_stock') * F('unit_cost'))
            )['total_value'] or 0
            context['total_inventory_value'] = total_inventory_value
            
        except ImportError:
            context['low_stock_count'] = 0
            context['low_stock_supplies'] = []
            context['total_inventory_value'] = 0
        
        # Performance Metrics
        context['performance_metrics'] = {
            'farm_utilization': round(
                ((context['total_allocated_area'] / context['total_area']) * 100) if context['total_area'] > 0 else 0, 1
            ),
            'avg_block_size': round(
                context['total_allocated_area'] / context['total_blocks'] if context['total_blocks'] > 0 else 0, 2
            ),
            'farmers_per_hectare': round(
                context['total_farmers'] / context['total_area'] if context['total_area'] > 0 else 0, 2
            )
        }
        
        # User role context
        context['user_role'] = user.role
        context['is_superuser'] = user.is_superuser
        context['user_farms'] = user_farms
        
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'


class RecommendationsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/recommendations.html'


# API Views for Dynamic Form Loading
class FarmBlocksAPIView(FarmAccessMixin, View):
    """
    API endpoint to get blocks for a specific farm
    """
    def get(self, request, farm_id):
        user = request.user
        
        # Get the farm and check access
        farm = get_object_or_404(Farm, id=farm_id)
        
        # Check if user has access to this farm
        if not user.is_superuser:
            if hasattr(user, 'role'):
                if user.role == 'farm_owner' and farm.owner != user:
                    return JsonResponse({'error': 'Access denied'}, status=403)
                elif user.role == 'farm_manager' and not farm.staff_members.filter(id=user.id).exists() and farm.owner != user:
                    return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get blocks for this farm
        blocks = Block.objects.filter(farm=farm, is_active=True).values('id', 'name')
        return JsonResponse(list(blocks), safe=False)


class CropVarietiesAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get varieties for a specific crop
    """
    def get(self, request, crop_id):
        crop = get_object_or_404(Crop, id=crop_id)
        varieties = CropVariety.objects.filter(crop=crop, is_active=True).values('id', 'name')
        return JsonResponse(list(varieties), safe=False)