from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class ReportCategory(models.Model):
    CATEGORY_CHOICES = [
        ('financial', 'Financial Reports'),
        ('production', 'Production Reports'),
        ('operational', 'Operational Reports'),
        ('marketplace', 'Marketplace Reports'),
        ('executive', 'Executive Reports'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Report Categories"
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

class Report(models.Model):
    REPORT_TYPES = [
        # Financial Reports
        ('budget_vs_actual', 'Budget vs Actual Analysis'),
        ('profit_loss', 'Profit & Loss Statement'),
        ('cost_analysis', 'Cost Analysis Report'),
        ('cash_flow', 'Cash Flow Report'),
        ('financial_summary', 'Financial Summary'),
        
        # Production Reports
        ('yield_analysis', 'Yield Analysis Report'),
        ('crop_performance', 'Crop Performance Report'),
        ('seasonal_comparison', 'Seasonal Comparison Report'),
        ('block_efficiency', 'Block Efficiency Report'),
        ('farmer_performance', 'Farmer Performance Report'),
        
        # Operational Reports
        ('activity_completion', 'Activity Completion Report'),
        ('task_management', 'Task Management Report'),
        ('equipment_utilization', 'Equipment Utilization Report'),
        ('inventory_report', 'Inventory Status Report'),
        ('staff_productivity', 'Staff Productivity Report'),
        
        # Marketplace Reports
        ('sales_performance', 'Sales Performance Report'),
        ('market_analysis', 'Market Price Analysis'),
        ('transaction_report', 'Transaction Report'),
        ('customer_analysis', 'Customer Analysis Report'),
        
        # Executive Reports
        ('executive_dashboard', 'Executive Dashboard'),
        ('kpi_scorecard', 'KPI Scorecard'),
        ('organization_overview', 'Organization Overview'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE, related_name='reports')
    description = models.TextField(blank=True)
    
    # Report parameters
    date_from = models.DateField()
    date_to = models.DateField()
    filters = models.JSONField(default=dict, blank=True)
    
    # Report metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    
    # Report status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['organization']),
            models.Index(fields=['farm']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"
    
    def mark_as_generating(self):
        self.status = 'generating'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_completed(self, data=None):
        self.status = 'completed'
        self.generated_at = timezone.now()
        if data:
            self.data = data
        self.save(update_fields=['status', 'generated_at', 'data', 'updated_at'])
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])

class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=Report.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Schedule parameters
    is_active = models.BooleanField(default=True)
    filters = models.JSONField(default=dict, blank=True)
    recipients = models.ManyToManyField(User, related_name='report_schedules')
    
    # Scheduling details
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='report_schedules', null=True, blank=True)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='report_schedules', null=True, blank=True)
    
    # Execution tracking
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"

class ReportExport(models.Model):
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Store the actual file content (for demo purposes)
    file_content = models.TextField(blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_exports')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['report', 'export_format']
    
    def __str__(self):
        return f"{self.report.name} - {self.get_export_format_display()}"
    
    def mark_as_completed(self, file_path, file_size=None):
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'file_path', 'file_size', 'completed_at', 'file_content', 'content_type'])
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

class ReportTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=Report.REPORT_TYPES)
    template_content = models.TextField()
    is_default = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_templates')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='report_templates', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['report_type', 'name']
        unique_together = ['report_type', 'organization', 'is_default']
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"