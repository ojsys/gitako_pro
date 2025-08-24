from django import forms
from .models import Budget, BudgetCategory, BudgetItem, IncomeItem, ExpenseItem
from apps.farms.models import Farm, Block
from apps.calendar.models import CropCalendar


class BudgetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['budget_type'].empty_label = "Select budget type"
        self.fields['status'].empty_label = "Select status"
        self.fields['farm'].empty_label = "Select a farm"
        self.fields['block'].empty_label = "Select a block (optional)"
        self.fields['calendar'].empty_label = "Select a calendar (optional)"
        
        # Set querysets for dependent fields based on user's accessible farms
        user_farms = self.fields['farm'].queryset
        self.fields['block'].queryset = Block.objects.filter(
            farm__in=user_farms, is_active=True
        )
        self.fields['calendar'].queryset = CropCalendar.objects.filter(
            farm__in=user_farms, is_active=True
        )
        
        # If this is an existing budget (edit mode), no need to change querysets
        # as they are already filtered by user's accessible farms
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                self.fields['farm'].queryset = Farm.objects.filter(is_active=True)
            elif user.role == 'farm_owner':
                self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Get farms where user is owner OR assigned as staff
                from apps.farms.models import FarmStaff
                owned_farms = Farm.objects.filter(owner=user, is_active=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
                
                farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
                self.fields['farm'].queryset = Farm.objects.filter(id__in=farm_ids, is_active=True).distinct()
            else:
                # Default to no farms if role is not recognized
                self.fields['farm'].queryset = Farm.objects.none()
        else:
            # If no user provided, show no farms
            self.fields['farm'].queryset = Farm.objects.none()
    
    def clean_block(self):
        """Custom validation for block field"""
        block = self.cleaned_data.get('block')
        farm = self.cleaned_data.get('farm')
        
        if block and farm:
            # Verify that the selected block belongs to the selected farm
            if block.farm != farm:
                raise forms.ValidationError("Selected block does not belong to the selected farm.")
        
        return block
    
    def clean_calendar(self):
        """Custom validation for calendar field"""
        calendar = self.cleaned_data.get('calendar')
        farm = self.cleaned_data.get('farm')
        
        if calendar and farm:
            # Verify that the selected calendar belongs to the selected farm
            if calendar.farm != farm:
                raise forms.ValidationError("Selected calendar does not belong to the selected farm.")
        
        return calendar

    class Meta:
        model = Budget
        fields = ['name', 'description', 'budget_type', 'status', 'farm', 'block', 'calendar', 'start_date', 'end_date', 'expected_yield', 'expected_price_per_unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Budget name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Budget description'}),
            'budget_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'block': forms.Select(attrs={'class': 'form-select'}),
            'calendar': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected yield in tons'}),
            'expected_price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Price per unit'}),
        }


class BudgetItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['budget'].empty_label = "Select a budget"
        self.fields['category'].empty_label = "Select a category"
        self.fields['item_type'].empty_label = "Select item type"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                self.fields['budget'].queryset = Budget.objects.all()
            elif user.role == 'farm_owner':
                self.fields['budget'].queryset = Budget.objects.filter(farm__owner=user)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Get budgets for farms where user is owner OR assigned as staff
                from apps.farms.models import FarmStaff
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                all_farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                self.fields['budget'].queryset = Budget.objects.filter(farm_id__in=all_farm_ids).distinct()
            else:
                self.fields['budget'].queryset = Budget.objects.none()

    class Meta:
        model = BudgetItem
        fields = ['budget', 'category', 'item_type', 'main_category', 'sub_category', 
                 # Excel-matching fields
                 'sequence_number', 'particulars', 'name', 'description', 'company', 'product_brand_name', 
                 'units', 'quantity', 'rate_per_unit', 'total_cost_per_ha',
                 # Income-specific fields
                 'expected_yield', 'actual_yield', 'market_price', 'buyer_name', 'sale_date', 'payment_status',
                 # Additional fields
                 'planned_amount', 'actual_amount', 'planned_date', 'actual_date', 
                 'supplier_vendor', 'payment_method', 'receipt_number', 'is_recurring', 'is_essential', 'notes']
        widgets = {
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'main_category': forms.Select(attrs={'class': 'form-select'}),
            'sub_category': forms.Select(attrs={'class': 'form-select'}),
            
            # Excel-matching fields
            'sequence_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'S.No.'}),
            'particulars': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category/type (e.g., Seed, Herbicide, NPK)'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description/Item name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional description'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name (e.g., Haike, Mongul)'}),
            'product_brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Brand Name (e.g., FARO 44, NPK 27:10:10)'}),
            'units': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Units (kg, bags, ltr, ha)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Quantity'}),
            'rate_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Rate per (Bag/Kg/Ltr)'}),
            'total_cost_per_ha': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Auto-calculated', 'readonly': True}),
            
            # Income-specific fields
            'expected_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected yield'}),
            'actual_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Actual yield achieved'}),
            'market_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Current market price'}),
            'buyer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buyer/customer name'}),
            'sale_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            
            # Additional fields
            'planned_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'actual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'planned_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier_vendor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier/vendor name'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment method'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receipt/invoice number'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_essential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }


class IncomeItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['budget'].empty_label = "Select a budget"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                self.fields['budget'].queryset = Budget.objects.all()
            elif user.role == 'farm_owner':
                self.fields['budget'].queryset = Budget.objects.filter(farm__owner=user)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Get budgets for farms where user is owner OR assigned as staff
                from apps.farms.models import FarmStaff
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                all_farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                self.fields['budget'].queryset = Budget.objects.filter(farm_id__in=all_farm_ids).distinct()
            else:
                self.fields['budget'].queryset = Budget.objects.none()

    class Meta:
        model = IncomeItem
        fields = ['budget', 'name', 'description', 'planned_amount', 'actual_amount', 'planned_yield', 'actual_yield', 'planned_price', 'actual_price', 'buyer', 'sale_date']
        widgets = {
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Income source name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Income description'}),
            'planned_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'actual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'planned_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected yield'}),
            'actual_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Actual yield'}),
            'planned_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected price per unit'}),
            'actual_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Actual price per unit'}),
            'buyer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buyer name'}),
            'sale_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ExpenseItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['budget'].empty_label = "Select a budget"
        self.fields['category'].empty_label = "Select a category"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                self.fields['budget'].queryset = Budget.objects.all()
            elif user.role == 'farm_owner':
                self.fields['budget'].queryset = Budget.objects.filter(farm__owner=user)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Get budgets for farms where user is owner OR assigned as staff
                from apps.farms.models import FarmStaff
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                all_farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                self.fields['budget'].queryset = Budget.objects.filter(farm_id__in=all_farm_ids).distinct()
            else:
                self.fields['budget'].queryset = Budget.objects.none()

    class Meta:
        model = ExpenseItem
        fields = ['budget', 'category', 'name', 'description', 'planned_amount', 'actual_amount', 'supplier', 'expense_date', 'receipt_number']
        widgets = {
            'budget': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expense name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Expense description'}),
            'planned_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'actual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receipt/invoice number'}),
        }