from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from .models import Supply, SupplyCategory, StockMovement, Equipment, MaintenanceRecord, PurchaseOrder
from apps.farms.models import Farm
from .forms import StockMovementForm


class SupplyListView(LoginRequiredMixin, ListView):
    model = Supply
    template_name = 'inventory/supplies.html'
    context_object_name = 'supplies'
    paginate_by = 20

    def get_queryset(self):
        queryset = Supply.objects.filter(is_active=True).select_related('category')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(brand__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Stock status filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(current_stock__lte=F('minimum_stock'))
        elif stock_status == 'out':
            queryset = queryset.filter(current_stock=0)
        
        return queryset.order_by('category__name', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get categories for filter dropdown
        context['categories'] = SupplyCategory.objects.filter(is_active=True).order_by('name')
        
        # Get summary statistics
        context['total_supplies'] = Supply.objects.filter(is_active=True).count()
        context['low_stock_count'] = Supply.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        ).count()
        context['out_of_stock_count'] = Supply.objects.filter(
            is_active=True,
            current_stock=0
        ).count()
        
        # Calculate total inventory value
        total_value = Supply.objects.filter(
            is_active=True,
            unit_cost__isnull=False
        ).aggregate(
            total=Sum(F('current_stock') * F('unit_cost'))
        )['total'] or 0
        context['total_inventory_value'] = total_value
        
        # Get recent stock movements
        context['recent_movements'] = StockMovement.objects.select_related(
            'supply', 'farm', 'recorded_by'
        ).order_by('-movement_date')[:5]
        
        return context


class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'inventory/equipment.html'
    context_object_name = 'equipment'
    paginate_by = 20

    def get_queryset(self):
        return Equipment.objects.filter(
            farm__owner=self.request.user,
            is_active=True
        ).select_related('farm', 'assigned_to').order_by('equipment_type', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_equipment = Equipment.objects.filter(farm__owner=self.request.user, is_active=True)
        
        # Get summary statistics
        context['total_equipment'] = user_equipment.count()
        context['operational_count'] = user_equipment.filter(status='operational').count()
        context['maintenance_due_count'] = user_equipment.filter(
            next_maintenance_date__lte=timezone.now().date()
        ).count()
        context['under_repair_count'] = user_equipment.filter(status='repair').count()
        
        # Get maintenance alerts
        context['maintenance_alerts'] = user_equipment.filter(
            next_maintenance_date__lte=timezone.now().date() + timezone.timedelta(days=7)
        ).order_by('next_maintenance_date')[:5]
        
        return context


class StockMovementCreateView(LoginRequiredMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock_movement_form.html'
    success_url = reverse_lazy('inventory:supplies')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, f'Stock movement recorded successfully!')
        return super().form_valid(form)