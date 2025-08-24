from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from .models import Budget, BudgetCategory, IncomeItem, ExpenseItem, BudgetItem
from apps.farms.models import Farm, Block
from apps.calendar.models import CropCalendar
from .forms import BudgetForm, BudgetItemForm, IncomeItemForm, ExpenseItemForm


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
        
        # Get legacy items
        context['income_items'] = self.object.income_items.all().order_by('-planned_amount')
        context['expense_items'] = self.object.expense_items.all().order_by('-planned_amount')
        
        # Get new BudgetItems (Excel-style items)
        context['budget_income_items'] = self.object.items.filter(item_type='income').order_by('-planned_amount')
        context['budget_expense_items'] = self.object.items.filter(item_type='expense').order_by('sequence_number', '-planned_amount')
        
        # Get all items combined for comprehensive view
        all_expense_items = list(context['expense_items']) + list(context['budget_expense_items'])
        all_income_items = list(context['income_items']) + list(context['budget_income_items'])
        
        context['all_expense_items'] = sorted(all_expense_items, key=lambda x: getattr(x, 'planned_amount', 0), reverse=True)
        context['all_income_items'] = sorted(all_income_items, key=lambda x: getattr(x, 'planned_amount', 0), reverse=True)
        
        # Calculate category-wise expenses (including both old and new items)
        expense_by_category = self.object.expense_items.values(
            'category__name'
        ).annotate(
            total_planned=Sum('planned_amount'),
            total_actual=Sum('actual_amount')
        ).order_by('-total_planned')
        
        # Add BudgetItem categories
        budget_expense_by_category = self.object.items.filter(item_type='expense').values(
            'category__name'
        ).annotate(
            total_planned=Sum('planned_amount'),
            total_actual=Sum('actual_amount')
        ).order_by('-total_planned')
        
        # Combine categories
        combined_categories = {}
        for category in expense_by_category:
            name = category['category__name']
            combined_categories[name] = {
                'category__name': name,
                'total_planned': category['total_planned'] or 0,
                'total_actual': category['total_actual'] or 0
            }
        
        for category in budget_expense_by_category:
            name = category['category__name']
            if name in combined_categories:
                combined_categories[name]['total_planned'] += category['total_planned'] or 0
                combined_categories[name]['total_actual'] += category['total_actual'] or 0
            else:
                combined_categories[name] = {
                    'category__name': name,
                    'total_planned': category['total_planned'] or 0,
                    'total_actual': category['total_actual'] or 0
                }
        
        context['expense_by_category'] = sorted(combined_categories.values(), key=lambda x: x['total_planned'], reverse=True)
        
        # Enhanced Analytics and KPIs
        budget = self.object
        
        # Profitability Analysis
        planned_profit = budget.total_planned_income - budget.total_planned_expenses
        actual_profit = budget.total_actual_income - budget.total_actual_expenses
        profit_margin = (planned_profit / budget.total_planned_income * 100) if budget.total_planned_income > 0 else 0
        
        context['planned_profit'] = planned_profit
        context['actual_profit'] = actual_profit
        context['profit_margin'] = profit_margin
        context['profit_variance'] = actual_profit - planned_profit
        
        # Budget Performance KPIs
        expense_variance = budget.total_actual_expenses - budget.total_planned_expenses
        income_variance = budget.total_actual_income - budget.total_planned_income
        budget_utilization = (budget.total_actual_expenses / budget.total_planned_expenses * 100) if budget.total_planned_expenses > 0 else 0
        income_achievement = (budget.total_actual_income / budget.total_planned_income * 100) if budget.total_planned_income > 0 else 0
        
        context['expense_variance'] = expense_variance
        context['income_variance'] = income_variance
        context['budget_utilization'] = budget_utilization
        context['income_achievement'] = income_achievement
        
        # Yield and Production Analytics (from Excel-style income items)
        excel_income_items = budget.items.filter(item_type='income')
        total_expected_yield = sum(item.expected_yield or 0 for item in excel_income_items)
        total_actual_yield = sum(item.actual_yield or 0 for item in excel_income_items)
        yield_efficiency = (total_actual_yield / total_expected_yield * 100) if total_expected_yield > 0 else 0
        
        context['total_expected_yield'] = total_expected_yield
        context['total_actual_yield'] = total_actual_yield
        context['yield_efficiency'] = yield_efficiency
        
        # Cost per hectare analysis
        if budget.block and budget.block.size:
            context['cost_per_hectare'] = budget.total_planned_expenses / budget.block.size
            context['revenue_per_hectare'] = budget.total_planned_income / budget.block.size
            context['profit_per_hectare'] = planned_profit / budget.block.size
        else:
            context['cost_per_hectare'] = budget.total_planned_expenses
            context['revenue_per_hectare'] = budget.total_planned_income
            context['profit_per_hectare'] = planned_profit
        
        # Payment Status Analysis (for Excel income items)
        payment_status_counts = {}
        for item in excel_income_items:
            status = item.payment_status or 'pending'
            payment_status_counts[status] = payment_status_counts.get(status, 0) + 1
        
        context['payment_status_counts'] = payment_status_counts
        
        # Category-wise insights
        excel_expense_items = budget.items.filter(item_type='expense')
        
        # Top expense categories
        category_totals = {}
        for item in excel_expense_items:
            main_cat = item.get_main_category_display()
            category_totals[main_cat] = category_totals.get(main_cat, 0) + (item.total_cost_per_ha or item.planned_amount or 0)
        
        context['top_expense_categories'] = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return context


class EnhancedBudgetSummaryView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budget/enhanced_summary.html'
    context_object_name = 'budget'

    def get_queryset(self):
        user = self.request.user
        
        # Apply same role-based filtering as detail view
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
        budget = self.object
        
        # Get all budget items for this budget
        budget_items = BudgetItem.objects.filter(
            budget=budget, item_type='expense'
        ).select_related('category').order_by('main_category', 'sub_category', 'name')
        
        # For backward compatibility, also get expense items if no budget items exist
        expense_items = budget.expense_items.all().select_related('category').order_by('category__name', 'name')
        
        # Organize items by main category and subcategory
        categorized_items = defaultdict(lambda: {
            'display_name': '',
            'subcategories': defaultdict(list),
            'total': 0
        })
        
        total_cost = 0
        
        # Process BudgetItems if they exist
        if budget_items.exists():
            for item in budget_items:
                main_cat = item.main_category
                sub_cat = item.sub_category
                
                # Set display name for main category
                if not categorized_items[main_cat]['display_name']:
                    categorized_items[main_cat]['display_name'] = item.get_main_category_display()
                
                # Add item to appropriate subcategory
                categorized_items[main_cat]['subcategories'][sub_cat].append(item)
                
                # Calculate totals
                item_cost = item.cost_per_hectare
                categorized_items[main_cat]['total'] += item_cost
                total_cost += item_cost
        
        # If no BudgetItems, use ExpenseItems for backward compatibility
        elif expense_items.exists():
            # Group expense items under "Other Expenses" category
            categorized_items['other']['display_name'] = 'Other Expenses'
            for expense_item in expense_items:
                # Create a wrapper to make expense items compatible with the template
                expense_wrapper = type('ExpenseWrapper', (), {
                    'name': expense_item.name,
                    'product_name': '',
                    'company_brand': expense_item.supplier,
                    'unit': '',
                    'planned_quantity': '',
                    'rate_per_unit': '',
                    'cost_per_hectare': expense_item.planned_amount,
                    'get_sub_category_display': lambda: expense_item.category.name if expense_item.category else 'General'
                })()
                
                categorized_items['other']['subcategories']['general'].append(expense_wrapper)
                categorized_items['other']['total'] += expense_item.planned_amount
                total_cost += expense_item.planned_amount
        
        context['categorized_items'] = dict(categorized_items)
        context['total_cost_per_hectare'] = total_cost
        
        # Calculate cost per hectare based on farm/block size
        if budget.block and budget.block.size:
            context['cost_per_hectare'] = budget.total_planned_expenses / budget.block.size
        else:
            context['cost_per_hectare'] = budget.total_planned_expenses
        
        return context


class BudgetItemCreateView(LoginRequiredMixin, CreateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'budget/budget_item_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            try:
                budget = self.get_user_budgets().get(id=budget_id)
                initial['budget'] = budget.pk  # Use primary key instead of object
                # Auto-set sequence number
                last_item = BudgetItem.objects.filter(budget=budget).order_by('-sequence_number').first()
                initial['sequence_number'] = (last_item.sequence_number + 1) if last_item else 1
                # Default values
                initial['item_type'] = 'expense'
                initial['is_essential'] = True
                # Set default category if available
                default_category = BudgetCategory.objects.filter(is_active=True).first()
                if default_category:
                    initial['category'] = default_category.pk
                # Set default main category
                initial['main_category'] = 'input_cost'
                initial['sub_category'] = 'other'
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            try:
                context['budget'] = self.get_user_budgets().get(id=budget_id)
            except Budget.DoesNotExist:
                context['budget'] = None
        return context
    
    def form_valid(self, form):
        # Verify user has access to the selected budget
        budget = form.cleaned_data['budget']
        if budget not in self.get_user_budgets():
            messages.error(self.request, 'You do not have permission to add items to this budget.')
            return self.form_invalid(form)
        
        # Set the created_by field
        form.instance.created_by = self.request.user
        
        # Ensure proper linking to budget
        form.instance.budget = budget
        
        # Debug logging
        print(f"Creating budget item for budget: {budget.name} (ID: {budget.pk})")
        print(f"Item details: {form.cleaned_data.get('name')} - {form.cleaned_data.get('total_cost_per_ha')}")
        
        response = super().form_valid(form)
        
        # Force budget recalculation after saving
        budget.recalculate_totals()
        
        messages.success(self.request, f'Budget item "{self.object.name}" added successfully to {budget.name}!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('budget:enhanced_summary', kwargs={'pk': self.object.budget.pk})


class BudgetIncomeItemCreateView(LoginRequiredMixin, CreateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'budget/budget_income_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            try:
                budget = self.get_user_budgets().get(id=budget_id)
                initial['budget'] = budget.pk
                # Auto-set sequence number for income
                last_item = BudgetItem.objects.filter(budget=budget, item_type='income').order_by('-sequence_number').first()
                initial['sequence_number'] = (last_item.sequence_number + 1) if last_item else 1
                # Default values for income
                initial['item_type'] = 'income'
                initial['is_essential'] = True
                # Set default category if available
                default_category = BudgetCategory.objects.filter(is_active=True).first()
                if default_category:
                    initial['category'] = default_category.pk
                # Set default main category for income
                initial['main_category'] = 'other'
                initial['sub_category'] = 'other'
                initial['payment_status'] = 'pending'
                initial['particulars'] = 'Agricultural Product'
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            try:
                context['budget'] = self.get_user_budgets().get(id=budget_id)
            except Budget.DoesNotExist:
                context['budget'] = None
        return context
    
    def form_valid(self, form):
        # Verify user has access to the selected budget
        budget = form.cleaned_data['budget']
        if budget not in self.get_user_budgets():
            messages.error(self.request, 'You do not have permission to add items to this budget.')
            return self.form_invalid(form)
        
        # Set the created_by field
        form.instance.created_by = self.request.user
        
        # Ensure proper linking to budget
        form.instance.budget = budget
        
        # Auto-calculate revenue if yield and price are provided
        if form.instance.expected_yield and form.instance.market_price:
            form.instance.total_cost_per_ha = form.instance.expected_yield * form.instance.market_price
            form.instance.planned_amount = form.instance.total_cost_per_ha
        
        response = super().form_valid(form)
        
        # Force budget recalculation after saving
        budget.recalculate_totals()
        
        messages.success(self.request, f'Income item "{self.object.name}" added successfully to {budget.name}!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('budget:detail', kwargs={'pk': self.object.budget.pk})


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