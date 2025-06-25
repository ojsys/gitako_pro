from django import forms
from .models import Supply, SupplyCategory, StockMovement, Equipment, MaintenanceRecord, PurchaseOrder
from apps.farms.models import Farm


class SupplyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['category'].empty_label = "Select a category"
        self.fields['unit_type'].empty_label = "Select unit type"

    class Meta:
        model = Supply
        fields = ['name', 'description', 'category', 'brand', 'model_number', 'unit_type', 'current_stock', 'minimum_stock', 'maximum_stock', 'unit_cost', 'supplier', 'supplier_contact', 'expiry_tracking', 'storage_location', 'storage_conditions', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supply name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand name'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model/SKU'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'maximum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'supplier_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone or email'}),
            'expiry_tracking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Storage location'}),
            'storage_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special storage requirements'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }


class StockMovementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['supply'].empty_label = "Select a supply"
        self.fields['movement_type'].empty_label = "Select movement type"
        self.fields['farm'].empty_label = "Select a farm"
        
        # Filter queryset based on user
        if user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)

    class Meta:
        model = StockMovement
        fields = ['supply', 'movement_type', 'quantity', 'unit_cost', 'reference_number', 'description', 'farm', 'supplier_vendor', 'expiry_date', 'batch_number']
        widgets = {
            'supply': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PO, Invoice, or reference number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Movement description'}),
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'supplier_vendor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier/vendor name'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch/lot number'}),
        }


class EquipmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['equipment_type'].empty_label = "Select equipment type"
        self.fields['status'].empty_label = "Select status"
        self.fields['farm'].empty_label = "Select a farm"
        self.fields['assigned_to'].empty_label = "Select assignee"
        
        # Filter queryset based on user
        if user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)

    class Meta:
        model = Equipment
        fields = ['name', 'description', 'equipment_type', 'status', 'farm', 'brand', 'model', 'serial_number', 'purchase_date', 'purchase_cost', 'current_value', 'supplier', 'warranty_expiry', 'location', 'assigned_to', 'last_maintenance_date', 'next_maintenance_date', 'maintenance_interval_days', 'operating_hours', 'fuel_type', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Equipment description'}),
            'equipment_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand name'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial number'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current location'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'last_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'maintenance_interval_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Days between maintenance'}),
            'operating_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': '0.0'}),
            'fuel_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fuel type'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }