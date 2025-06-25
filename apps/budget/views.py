from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Budget, BudgetCategory, IncomeItem, ExpenseItem
from apps.farms.models import Farm, Block
from apps.calendar.models import CropCalendar
from .forms import BudgetForm, IncomeItemForm, ExpenseItemForm


class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budget/list.html'
    context_object_name = 'budgets'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        
        # Get user's accessible farms based on role
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.select_related('farm', 'calendar').order_by('-start_date')
        elif user.role == 'farm_owner':
            return Budget.objects.filter(
                farm__owner=user
            ).select_related('farm', 'calendar').order_by('-start_date')
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Get budgets for farms where user is owner OR assigned as staff
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(
                farm_id__in=farm_ids
            ).select_related('farm', 'calendar').order_by('-start_date').distinct()
        else:
            return Budget.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get budget summary statistics for user's accessible budgets
        user_budgets = self.get_queryset()
        context['total_budgets'] = user_budgets.count()
        context['active_budgets'] = user_budgets.filter(status='active').count()
        
        # Calculate totals
        totals = user_budgets.aggregate(
            total_planned_income=Sum('total_planned_income'),
            total_actual_income=Sum('total_actual_income'),
            total_planned_expenses=Sum('total_planned_expenses'),
            total_actual_expenses=Sum('total_actual_expenses')
        )
        
        context['summary'] = {
            'planned_profit': (totals['total_planned_income'] or 0) - (totals['total_planned_expenses'] or 0),
            'actual_profit': (totals['total_actual_income'] or 0) - (totals['total_actual_expenses'] or 0),
            'total_planned_income': totals['total_planned_income'] or 0,
            'total_actual_income': totals['total_actual_income'] or 0,
            'total_planned_expenses': totals['total_planned_expenses'] or 0,
            'total_actual_expenses': totals['total_actual_expenses'] or 0,
        }
        
        return context


class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budget/detail.html'
    context_object_name = 'budget'

    def get_queryset(self):
        user = self.request.user
        
        # Apply same role-based filtering as list view
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Get budgets for farms where user is owner OR assigned as staff
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['income_items'] = self.object.income_items.all().order_by('-planned_amount')
        context['expense_items'] = self.object.expense_items.all().order_by('-planned_amount')
        
        # Calculate category-wise expenses
        expense_by_category = self.object.expense_items.values(
            'category__name'
        ).annotate(
            total_planned=Sum('planned_amount'),
            total_actual=Sum('actual_amount')
        ).order_by('-total_planned')
        context['expense_by_category'] = expense_by_category
        
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/create.html'
    success_url = reverse_lazy('budget:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_form(self, form_class=None):
        """Override to handle dynamic queryset updates based on submitted data"""
        form = super().get_form(form_class)
        
        # If this is a POST request, update the querysets based on submitted farm
        if self.request.method == 'POST':
            farm_id = self.request.POST.get('farm')
            if farm_id:
                try:
                    # Verify user has access to this farm
                    user_farms = form.fields['farm'].queryset
                    selected_farm = user_farms.get(id=farm_id)
                    
                    # Update dependent field querysets
                    form.fields['block'].queryset = Block.objects.filter(
                        farm=selected_farm, is_active=True
                    )
                    form.fields['calendar'].queryset = CropCalendar.objects.filter(
                        farm=selected_farm, is_active=True
                    )
                except (Farm.DoesNotExist, ValueError):
                    # If farm doesn't exist or user doesn't have access, keep original querysets
                    pass
        
        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Budget created successfully!')
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/create.html'  # Reuse create template
    success_url = reverse_lazy('budget:list')
    
    def get_queryset(self):
        user = self.request.user
        
        # Apply same role-based filtering as other views
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Get budgets for farms where user is owner OR assigned as staff
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_form(self, form_class=None):
        """Override to handle dynamic queryset updates based on submitted data"""
        form = super().get_form(form_class)
        
        # If this is a POST request, update the querysets based on submitted farm
        if self.request.method == 'POST':
            farm_id = self.request.POST.get('farm')
            if farm_id:
                try:
                    # Verify user has access to this farm
                    user_farms = form.fields['farm'].queryset
                    selected_farm = user_farms.get(id=farm_id)
                    
                    # Update dependent field querysets
                    form.fields['block'].queryset = Block.objects.filter(
                        farm=selected_farm, is_active=True
                    )
                    form.fields['calendar'].queryset = CropCalendar.objects.filter(
                        farm=selected_farm, is_active=True
                    )
                except (Farm.DoesNotExist, ValueError):
                    # If farm doesn't exist or user doesn't have access, keep original querysets
                    pass
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Budget updated successfully!')
        return super().form_valid(form)


@login_required
def load_blocks(request):
    """AJAX view to load blocks based on selected farm"""
    farm_id = request.GET.get('farm_id')
    blocks = Block.objects.filter(farm_id=farm_id, is_active=True).order_by('name')
    block_data = [{'id': block.id, 'name': block.name} for block in blocks]
    return JsonResponse({'blocks': block_data})


@login_required
def load_calendars(request):
    """AJAX view to load crop calendars based on selected farm"""
    farm_id = request.GET.get('farm_id')
    calendars = CropCalendar.objects.filter(farm_id=farm_id, is_active=True).order_by('-start_date')
    calendar_data = [
        {
            'id': calendar.id, 
            'name': calendar.name,
            'crop': calendar.crop.name if calendar.crop else '',
            'season': calendar.season_type,
            'year': calendar.season_year
        } 
        for calendar in calendars
    ]
    return JsonResponse({'calendars': calendar_data})


# =============== INCOME ITEM VIEWS ===============

class IncomeItemCreateView(LoginRequiredMixin, CreateView):
    model = IncomeItem
    form_class = IncomeItemForm
    template_name = 'budget/income_item_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            # Verify user has access to this budget
            try:
                budget = self.get_user_budgets().get(id=budget_id)
                initial['budget'] = budget
            except Budget.DoesNotExist:
                pass
        return initial
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def form_valid(self, form):
        # Verify user has access to the selected budget
        budget = form.cleaned_data['budget']
        if budget not in self.get_user_budgets():
            messages.error(self.request, 'You do not have permission to add items to this budget.')
            return self.form_invalid(form)
        
        messages.success(self.request, 'Income item added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('budget:detail', kwargs={'pk': self.object.budget.pk})


class IncomeItemUpdateView(LoginRequiredMixin, UpdateView):
    model = IncomeItem
    form_class = IncomeItemForm
    template_name = 'budget/income_item_form.html'
    
    def get_queryset(self):
        user = self.request.user
        user_budgets = self.get_user_budgets()
        return IncomeItem.objects.filter(budget__in=user_budgets)
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Income item updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('budget:detail', kwargs={'pk': self.object.budget.pk})


class IncomeItemDeleteView(LoginRequiredMixin, DetailView):
    model = IncomeItem
    template_name = 'budget/income_item_confirm_delete.html'
    
    def get_queryset(self):
        user = self.request.user
        user_budgets = self.get_user_budgets()
        return IncomeItem.objects.filter(budget__in=user_budgets)
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def post(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        self.object = self.get_object()
        budget_pk = self.object.budget.pk
        self.object.delete()
        messages.success(request, 'Income item deleted successfully!')
        return redirect('budget:detail', pk=budget_pk)


# =============== EXPENSE ITEM VIEWS ===============

class ExpenseItemCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseItem
    form_class = ExpenseItemForm
    template_name = 'budget/expense_item_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            # Verify user has access to this budget
            try:
                budget = self.get_user_budgets().get(id=budget_id)
                initial['budget'] = budget
            except Budget.DoesNotExist:
                pass
        return initial
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def form_valid(self, form):
        # Verify user has access to the selected budget
        budget = form.cleaned_data['budget']
        if budget not in self.get_user_budgets():
            messages.error(self.request, 'You do not have permission to add items to this budget.')
            return self.form_invalid(form)
        
        messages.success(self.request, 'Expense item added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('budget:detail', kwargs={'pk': self.object.budget.pk})


class ExpenseItemUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpenseItem
    form_class = ExpenseItemForm
    template_name = 'budget/expense_item_form.html'
    
    def get_queryset(self):
        user = self.request.user
        user_budgets = self.get_user_budgets()
        return ExpenseItem.objects.filter(budget__in=user_budgets)
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense item updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('budget:detail', kwargs={'pk': self.object.budget.pk})


class ExpenseItemDeleteView(LoginRequiredMixin, DetailView):
    model = ExpenseItem
    template_name = 'budget/expense_item_confirm_delete.html'
    
    def get_queryset(self):
        user = self.request.user
        user_budgets = self.get_user_budgets()
        return ExpenseItem.objects.filter(budget__in=user_budgets)
    
    def get_user_budgets(self):
        """Get budgets accessible to the current user"""
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Budget.objects.all()
        elif user.role == 'farm_owner':
            return Budget.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff, Farm
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
            
            farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
            return Budget.objects.filter(farm_id__in=farm_ids).distinct()
        else:
            return Budget.objects.none()
    
    def post(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        self.object = self.get_object()
        budget_pk = self.object.budget.pk
        self.object.delete()
        messages.success(request, 'Expense item deleted successfully!')
        return redirect('budget:detail', pk=budget_pk)