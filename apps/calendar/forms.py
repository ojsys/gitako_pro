from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from .models import CropCalendar, Activity, CalendarTemplate, ActivityTemplate
from apps.farms.models import Farm, Block, Crop, CropVariety

User = get_user_model()


class CropCalendarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['farm'].empty_label = "Select a farm"
        self.fields['block'].empty_label = "Select a block (optional)"
        self.fields['crop'].empty_label = "Select a crop"
        self.fields['variety'].empty_label = "Select a variety (optional)"
        self.fields['season_type'].empty_label = "Select season type"
        
        # If editing and there's a crop selected, filter varieties
        if self.instance.pk and self.instance.crop:
            self.fields['variety'].queryset = CropVariety.objects.filter(
                crop=self.instance.crop, is_active=True
            )
        else:
            # For new forms, start with no varieties until crop is selected
            self.fields['variety'].queryset = CropVariety.objects.none()
        
        # If editing and there's a farm selected, filter blocks
        if self.instance.pk and self.instance.farm:
            self.fields['block'].queryset = Block.objects.filter(
                farm=self.instance.farm, is_active=True
            )
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin see all farms
                self.fields['farm'].queryset = Farm.objects.filter(is_active=True)
                self.fields['block'].queryset = Block.objects.filter(is_active=True)
            elif user.role == 'farm_owner':
                # Farm owner sees their own farms
                self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)
                self.fields['block'].queryset = Block.objects.filter(farm__owner=user, is_active=True)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers see farms they're associated with
                from apps.farms.models import FarmStaff
                
                # Get farms where user is owner or staff member
                owned_farms = Farm.objects.filter(owner=user, is_active=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
                
                # Combine both querysets
                farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
                self.fields['farm'].queryset = Farm.objects.filter(id__in=farm_ids, is_active=True).distinct()
                self.fields['block'].queryset = Block.objects.filter(farm__id__in=farm_ids, is_active=True)
            else:
                # Default: no farms
                self.fields['farm'].queryset = Farm.objects.none()
                self.fields['block'].queryset = Block.objects.none()
        
        # Filter to active crops only
        self.fields['crop'].queryset = Crop.objects.filter(is_active=True)

    class Meta:
        model = CropCalendar
        fields = ['name', 'description', 'farm', 'block', 'crop', 'variety', 'season_type', 'season_year', 'start_date', 'expected_end_date', 'actual_end_date', 'is_template']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calendar name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Calendar description'}),
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'block': forms.Select(attrs={'class': 'form-select'}),
            'crop': forms.Select(attrs={'class': 'form-select'}),
            'variety': forms.Select(attrs={'class': 'form-select'}),
            'season_type': forms.Select(attrs={'class': 'form-select'}),
            'season_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2030', 'placeholder': '2024'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_template': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['calendar'].empty_label = "Select a calendar"
        self.fields['activity_type'].empty_label = "Select activity type"
        self.fields['priority'].empty_label = "Select priority"
        self.fields['status'].empty_label = "Select status"
        self.fields['assigned_to'].empty_label = "Select assignee (optional)"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin see all calendars
                self.fields['calendar'].queryset = CropCalendar.objects.all()
            elif user.role == 'farm_owner':
                # Farm owner sees their own calendars
                self.fields['calendar'].queryset = CropCalendar.objects.filter(farm__owner=user)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers see calendars for farms they're associated with
                from apps.farms.models import FarmStaff
                
                # Get farms where user is owner or staff member
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                # Combine farm IDs
                farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                self.fields['calendar'].queryset = CropCalendar.objects.filter(farm__id__in=farm_ids).distinct()
            else:
                # Default: no calendars
                self.fields['calendar'].queryset = CropCalendar.objects.none()
            
            # Filter assignable users based on role
            if user.is_superuser:
                self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
            else:
                # Show users who can work on farms user has access to
                farm_ids = self.fields['calendar'].queryset.values_list('farm_id', flat=True)
                from apps.farms.models import FarmStaff
                farm_users = User.objects.filter(
                    models.Q(owned_farms__id__in=farm_ids) | 
                    models.Q(farm_assignments__farm_id__in=farm_ids, farm_assignments__is_active=True)
                ).distinct()
                self.fields['assigned_to'].queryset = farm_users.filter(is_active=True)

    class Meta:
        model = Activity
        fields = ['calendar', 'name', 'description', 'activity_type', 'priority', 'status', 'scheduled_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date', 'assigned_to', 'estimated_cost', 'actual_cost', 'materials_needed', 'equipment_needed', 'labor_hours', 'actual_labor_hours', 'weather_dependent', 'notes']
        widgets = {
            'calendar': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Activity name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Activity description'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'materials_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of materials needed'}),
            'equipment_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of equipment needed'}),
            'labor_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Estimated hours'}),
            'actual_labor_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Actual hours'}),
            'weather_dependent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }


class CalendarTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['crop'].empty_label = "Select a crop"
        self.fields['variety'].empty_label = "Select a variety (optional)"
        self.fields['season_type'].empty_label = "Select season type"
        
        # Filter to active crops only
        self.fields['crop'].queryset = Crop.objects.filter(is_active=True)

    class Meta:
        model = CalendarTemplate
        fields = ['name', 'description', 'crop', 'variety', 'season_type', 'duration_days', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Template description'}),
            'crop': forms.Select(attrs={'class': 'form-select'}),
            'variety': forms.Select(attrs={'class': 'form-select'}),
            'season_type': forms.Select(attrs={'class': 'form-select'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Season duration in days'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ActivityTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['template'].empty_label = "Select a template"
        self.fields['activity_type'].empty_label = "Select activity type"
        self.fields['priority'].empty_label = "Select priority"

    class Meta:
        model = ActivityTemplate
        fields = ['template', 'name', 'description', 'activity_type', 'priority', 'days_from_start', 'duration_days', 'estimated_cost_per_hectare', 'materials_needed', 'equipment_needed', 'labor_hours_per_hectare', 'weather_dependent', 'is_critical']
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Activity name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Activity description'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'days_from_start': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Days from season start'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Activity duration in days'}),
            'estimated_cost_per_hectare': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Cost per hectare'}),
            'materials_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Materials needed'}),
            'equipment_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Equipment needed'}),
            'labor_hours_per_hectare': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Hours per hectare'}),
            'weather_dependent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_critical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }