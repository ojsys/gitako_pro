from django.contrib import admin
from .models import CropCalendar, Activity, ActivityLog, CalendarTemplate, ActivityTemplate


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CropCalendar)
class CropCalendarAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'crop', 'season_type', 'season_year', 'start_date', 'is_active')
    list_filter = ('season_type', 'season_year', 'is_active', 'crop', 'farm')
    search_fields = ('name', 'farm__name', 'crop__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ActivityInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'farm', 'block', 'crop', 'variety')
        }),
        ('Season Details', {
            'fields': ('season_type', 'season_year', 'start_date', 'expected_end_date', 'actual_end_date')
        }),
        ('Settings', {
            'fields': ('created_by', 'is_active', 'is_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'calendar', 'activity_type', 'priority', 'status', 'scheduled_date', 'assigned_to')
    list_filter = ('activity_type', 'priority', 'status', 'scheduled_date', 'weather_dependent')
    search_fields = ('name', 'calendar__name', 'assigned_to__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('calendar', 'name', 'description', 'activity_type', 'priority', 'status')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Assignment & Cost', {
            'fields': ('assigned_to', 'estimated_cost', 'actual_cost', 'labor_hours', 'actual_labor_hours')
        }),
        ('Resources', {
            'fields': ('materials_needed', 'equipment_needed')
        }),
        ('Additional Info', {
            'fields': ('weather_dependent', 'notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('activity', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('activity__name', 'user__email', 'description')
    readonly_fields = ('timestamp',)


class ActivityTemplateInline(admin.TabularInline):
    model = ActivityTemplate
    extra = 0


@admin.register(CalendarTemplate)
class CalendarTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'crop', 'season_type', 'duration_days', 'is_public', 'created_by')
    list_filter = ('crop', 'season_type', 'is_public')
    search_fields = ('name', 'crop__name', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ActivityTemplateInline]

    fieldsets = (
        ('Template Details', {
            'fields': ('name', 'description', 'crop', 'variety', 'season_type', 'duration_days')
        }),
        ('Access Control', {
            'fields': ('created_by', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityTemplate)
class ActivityTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'activity_type', 'days_from_start', 'duration_days', 'is_critical')
    list_filter = ('activity_type', 'priority', 'is_critical', 'weather_dependent')
    search_fields = ('name', 'template__name', 'template__crop__name')