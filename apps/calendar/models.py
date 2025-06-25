from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class CropCalendar(models.Model):
    class SeasonType(models.TextChoices):
        WET_SEASON = 'wet', 'Wet Season'
        DRY_SEASON = 'dry', 'Dry Season'
        ALL_YEAR = 'all_year', 'All Year Round'

    name = models.CharField(max_length=200, help_text="e.g., 2024 Wet Season Maize Calendar")
    description = models.TextField(blank=True)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='calendars')
    block = models.ForeignKey('farms.Block', on_delete=models.CASCADE, null=True, blank=True, related_name='calendars')
    crop = models.ForeignKey('farms.Crop', on_delete=models.CASCADE, related_name='calendars')
    variety = models.ForeignKey('farms.CropVariety', on_delete=models.SET_NULL, null=True, blank=True)
    season_type = models.CharField(max_length=20, choices=SeasonType.choices)
    season_year = models.PositiveIntegerField(default=timezone.now().year)
    
    start_date = models.DateField(help_text="Start of the farming season")
    expected_end_date = models.DateField(help_text="Expected end of the farming season")
    actual_end_date = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_calendars')
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False, help_text="Can be used as template for future seasons")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_cropcalendar'
        verbose_name = 'Crop Calendar'
        verbose_name_plural = 'Crop Calendars'
        ordering = ['-season_year', '-start_date']
        unique_together = ['farm', 'block', 'crop', 'season_year', 'season_type']

    def __str__(self):
        return f"{self.name} - {self.farm.name}"

    @property
    def progress_percentage(self):
        if not self.is_active:
            return 100
        
        total_days = (self.expected_end_date - self.start_date).days
        if total_days <= 0:
            return 0
            
        days_passed = (timezone.now().date() - self.start_date).days
        if days_passed <= 0:
            return 0
        elif days_passed >= total_days:
            return 100
        else:
            return int((days_passed / total_days) * 100)

    @property
    def total_activities(self):
        return self.activities.count()

    @property
    def completed_activities(self):
        return self.activities.filter(status='completed').count()


class Activity(models.Model):
    class ActivityType(models.TextChoices):
        LAND_PREPARATION = 'land_prep', 'Land Preparation'
        PLANTING = 'planting', 'Planting'
        FERTILIZER_APPLICATION = 'fertilizer', 'Fertilizer Application'
        WEEDING = 'weeding', 'Weeding'
        PEST_CONTROL = 'pest_control', 'Pest Control'
        DISEASE_CONTROL = 'disease_control', 'Disease Control'
        IRRIGATION = 'irrigation', 'Irrigation'
        PRUNING = 'pruning', 'Pruning'
        HARVESTING = 'harvesting', 'Harvesting'
        POST_HARVEST = 'post_harvest', 'Post Harvest'
        STORAGE = 'storage', 'Storage'
        MARKETING = 'marketing', 'Marketing'
        OTHER = 'other', 'Other'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        OVERDUE = 'overdue', 'Overdue'

    calendar = models.ForeignKey(CropCalendar, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    
    scheduled_date = models.DateField()
    scheduled_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_activities'
    )
    
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    materials_needed = models.TextField(blank=True, help_text="List of materials/inputs needed")
    equipment_needed = models.TextField(blank=True, help_text="List of equipment needed")
    labor_hours = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated labor hours")
    actual_labor_hours = models.PositiveIntegerField(null=True, blank=True)
    
    weather_dependent = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_activities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_activity'
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        ordering = ['scheduled_date', 'priority']

    def __str__(self):
        return f"{self.name} - {self.calendar.name}"

    @property
    def is_overdue(self):
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.scheduled_date

    @property
    def days_until_due(self):
        if self.status in ['completed', 'cancelled']:
            return None
        return (self.scheduled_date - timezone.now().date()).days

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.actual_end_date = timezone.now().date()
        self.save()

    def mark_in_progress(self):
        self.status = self.Status.IN_PROGRESS
        if not self.actual_start_date:
            self.actual_start_date = timezone.now().date()
        self.save()


class ActivityLog(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # created, started, completed, updated, etc.
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'calendar_activitylog'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity.name} - {self.action} by {self.user.full_name}"


class CalendarTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    crop = models.ForeignKey('farms.Crop', on_delete=models.CASCADE, related_name='templates')
    variety = models.ForeignKey('farms.CropVariety', on_delete=models.SET_NULL, null=True, blank=True)
    season_type = models.CharField(max_length=20, choices=CropCalendar.SeasonType.choices)
    duration_days = models.PositiveIntegerField(help_text="Total season duration in days")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False, help_text="Available to all users")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_calendartemplate'
        verbose_name = 'Calendar Template'
        verbose_name_plural = 'Calendar Templates'
        ordering = ['crop__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.crop.name}"


class ActivityTemplate(models.Model):
    template = models.ForeignKey(CalendarTemplate, on_delete=models.CASCADE, related_name='activity_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity_type = models.CharField(max_length=20, choices=Activity.ActivityType.choices)
    priority = models.CharField(max_length=10, choices=Activity.Priority.choices, default=Activity.Priority.MEDIUM)
    
    days_from_start = models.PositiveIntegerField(help_text="Days from season start when this activity should occur")
    duration_days = models.PositiveIntegerField(default=1, help_text="Duration of the activity in days")
    
    estimated_cost_per_hectare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    materials_needed = models.TextField(blank=True)
    equipment_needed = models.TextField(blank=True)
    labor_hours_per_hectare = models.PositiveIntegerField(null=True, blank=True)
    
    weather_dependent = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False, help_text="Critical activity that cannot be skipped")

    class Meta:
        db_table = 'calendar_activitytemplate'
        verbose_name = 'Activity Template'
        verbose_name_plural = 'Activity Templates'
        ordering = ['days_from_start']

    def __str__(self):
        return f"{self.name} (Day {self.days_from_start})"