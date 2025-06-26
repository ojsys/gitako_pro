from django.contrib import admin
from .models import ReportCategory, Report, ReportSchedule, ReportExport, ReportTemplate

@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'is_active', 'created_at']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category_type', 'name']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'status', 'created_by', 'organization', 'farm', 'created_at']
    list_filter = ['report_type', 'status', 'category', 'organization', 'farm']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'generated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'category', 'description')
        }),
        ('Parameters', {
            'fields': ('date_from', 'date_to', 'filters')
        }),
        ('Ownership', {
            'fields': ('created_by', 'organization', 'farm')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'generated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'last_run', 'next_run']
    list_filter = ['report_type', 'frequency', 'is_active', 'organization', 'farm']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['next_run']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'frequency', 'is_active')
        }),
        ('Parameters', {
            'fields': ('filters', 'recipients')
        }),
        ('Ownership', {
            'fields': ('created_by', 'organization', 'farm')
        }),
        ('Scheduling', {
            'fields': ('last_run', 'next_run')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['report', 'export_format', 'status', 'file_size', 'created_by', 'created_at']
    list_filter = ['export_format', 'status']
    search_fields = ['report__name', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'completed_at']
    ordering = ['-created_at']

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_default', 'organization', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_default', 'organization']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['report_type', 'name']