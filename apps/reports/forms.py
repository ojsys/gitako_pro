from django import forms
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Report, ReportCategory, ReportSchedule
from apps.farms.models import Farm, Crop
from apps.budget.models import BudgetCategory


class ReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default date range (last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        self.fields['date_from'].initial = start_date
        self.fields['date_to'].initial = end_date
        
        # Filter categories to active ones
        self.fields['category'].queryset = ReportCategory.objects.filter(is_active=True)
        
        # Filter farms based on user's role and access
        if self.user:
            if self.user.is_superuser:
                # Superusers can see all farms
                self.fields['farm'].queryset = Farm.objects.all()
                # Add empty option for superusers to select all farms
                self.fields['farm'].empty_label = "All farms"
            elif hasattr(self.user, 'role') and self.user.role == 'farm_owner':
                # Farm owners see their own farms
                self.fields['farm'].queryset = Farm.objects.filter(owner=self.user)
            elif hasattr(self.user, 'profile') and self.user.profile.organization:
                # Organization members see farms in their organization
                self.fields['farm'].queryset = Farm.objects.filter(
                    organization=self.user.profile.organization
                )
            else:
                # Check if user is assigned to any farm as staff
                try:
                    from apps.farms.models import FarmStaff
                    staff = FarmStaff.objects.get(user=self.user, is_active=True)
                    self.fields['farm'].queryset = Farm.objects.filter(id=staff.farm.id)
                except:
                    self.fields['farm'].queryset = Farm.objects.none()
        else:
            self.fields['farm'].queryset = Farm.objects.none()
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.DateInput, forms.Select, forms.Textarea)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
        
        # Set date widget type
        self.fields['date_from'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
        self.fields['date_to'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    
    # Filter fields for specific report types
    crop_filter = forms.ModelChoiceField(
        queryset=Crop.objects.all(),
        required=False,
        help_text="Filter by specific crop (optional)"
    )
    
    budget_category_filter = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.all(),
        required=False,
        help_text="Filter by budget category (optional)"
    )
    
    include_projections = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Include projected/budgeted amounts in addition to actual amounts"
    )
    
    group_by_month = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Group results by month for trend analysis"
    )
    
    class Meta:
        model = Report
        fields = [
            'name', 'report_type', 'category', 'description',
            'date_from', 'date_to', 'farm'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'report_type': forms.Select(attrs={'class': 'form-control report-type-select'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError("Start date must be before end date.")
            
            # Check if date range is reasonable (not more than 2 years)
            if (date_to - date_from).days > 730:
                raise forms.ValidationError("Date range cannot exceed 2 years.")
        
        return cleaned_data
    
    def save(self, commit=True):
        report = super().save(commit=False)
        
        # Build filters dictionary from form fields
        filters = {}
        
        if self.cleaned_data.get('crop_filter'):
            filters['crop_id'] = str(self.cleaned_data['crop_filter'].id)
        
        if self.cleaned_data.get('budget_category_filter'):
            filters['budget_category'] = self.cleaned_data['budget_category_filter'].name
        
        if self.cleaned_data.get('include_projections'):
            filters['include_projections'] = True
        
        if self.cleaned_data.get('group_by_month'):
            filters['group_by_month'] = True
        
        report.filters = filters
        
        if commit:
            report.save()
        
        return report


class ReportScheduleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter farms based on user's organization
        if self.user:
            if self.user.is_superuser:
                # Superusers can see all farms
                self.fields['farm'].queryset = Farm.objects.all()
                self.fields['farm'].empty_label = "All farms"
                # Superusers can add any user as recipient
                self.fields['recipients'].queryset = self.user.__class__.objects.all()
            elif hasattr(self.user, 'profile') and self.user.profile.organization:
                self.fields['farm'].queryset = Farm.objects.filter(
                    organization=self.user.profile.organization
                )
                # Set recipients to organization members
                organization = self.user.profile.organization
                self.fields['recipients'].queryset = organization.members.all()
            else:
                self.fields['farm'].queryset = Farm.objects.none()
                self.fields['recipients'].queryset = self.user.__class__.objects.filter(id=self.user.id)
        else:
            self.fields['farm'].queryset = Farm.objects.none()
            self.fields['recipients'].queryset = self.user.__class__.objects.none()
        
        # Set default next run time (tomorrow at 9 AM)
        tomorrow = timezone.now() + timedelta(days=1)
        default_next_run = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        self.fields['next_run'].initial = default_next_run
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.DateTimeInput, forms.Select, forms.Textarea)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})
        
        # Set datetime widget
        self.fields['next_run'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    
    # Additional filter fields
    filters_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text="JSON format filters for the scheduled report (optional)"
    )
    
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'report_type', 'frequency', 'is_active',
            'farm', 'recipients', 'next_run'
        ]
        widgets = {
            'recipients': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'})
        }
    
    def clean_filters_json(self):
        filters_json = self.cleaned_data.get('filters_json', '').strip()
        if filters_json:
            try:
                import json
                json.loads(filters_json)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format for filters.")
        return filters_json
    
    def clean_next_run(self):
        next_run = self.cleaned_data.get('next_run')
        if next_run and next_run <= timezone.now():
            raise forms.ValidationError("Next run time must be in the future.")
        return next_run
    
    def save(self, commit=True):
        schedule = super().save(commit=False)
        
        # Parse filters JSON if provided
        filters_json = self.cleaned_data.get('filters_json', '').strip()
        if filters_json:
            import json
            schedule.filters = json.loads(filters_json)
        else:
            schedule.filters = {}
        
        if commit:
            schedule.save()
            self.save_m2m()  # Save many-to-many relationships
        
        return schedule


class QuickReportForm(forms.Form):
    """Simplified form for quick report generation"""
    QUICK_REPORT_TYPES = [
        ('financial_summary', 'Financial Summary'),
        ('yield_analysis', 'Yield Analysis'),
        ('budget_vs_actual', 'Budget vs Actual'),
        ('cash_flow', 'Cash Flow'),
    ]
    
    PERIOD_CHOICES = [
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 3 months'),
        ('365', 'Last year'),
        ('custom', 'Custom range'),
    ]
    
    report_type = forms.ChoiceField(
        choices=QUICK_REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='30',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    farm = forms.ModelChoiceField(
        queryset=Farm.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter farms based on user's organization
        if self.user:
            if self.user.is_superuser:
                # Superusers can see all farms
                self.fields['farm'].queryset = Farm.objects.all()
                self.fields['farm'].empty_label = "All farms"
            elif hasattr(self.user, 'profile') and self.user.profile.organization:
                self.fields['farm'].queryset = Farm.objects.filter(
                    organization=self.user.profile.organization
                )
            else:
                self.fields['farm'].queryset = Farm.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if period == 'custom':
            if not date_from or not date_to:
                raise forms.ValidationError("Custom date range requires both start and end dates.")
            if date_from > date_to:
                raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data
    
    def get_date_range(self):
        """Calculate actual date range based on period selection"""
        period = self.cleaned_data.get('period')
        
        if period == 'custom':
            return self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        
        end_date = timezone.now().date()
        days = int(period)
        start_date = end_date - timedelta(days=days)
        
        return start_date, end_date


class ReportFilterForm(forms.Form):
    """Form for filtering report lists"""
    REPORT_STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search reports...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=ReportCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=REPORT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )