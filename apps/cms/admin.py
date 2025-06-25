from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SiteSettings, TeamMember, Testimonial, Feature, 
    PricingPlan, FAQ, Office, HeroSection, ContactSubmission
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'tagline', 'email', 'active_farmers', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'tagline', 'description', 'logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Social Media', {
            'fields': ('twitter_url', 'facebook_url', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Business Metrics', {
            'fields': ('active_farmers', 'hectares_managed', 'yield_increase_percentage', 'revenue_generated')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one SiteSettings instance
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of SiteSettings
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'role', 'is_active', 'sort_order']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'title', 'bio']
    list_editable = ['sort_order', 'is_active']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'role', 'bio', 'image')
        }),
        ('Contact & Social', {
            'fields': ('email', 'linkedin_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('sort_order', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_location', 'rating', 'is_featured', 'is_active', 'sort_order']
    list_filter = ['rating', 'is_featured', 'is_active', 'created_at']
    search_fields = ['customer_name', 'customer_location', 'testimonial_text']
    list_editable = ['is_featured', 'is_active', 'sort_order']
    ordering = ['sort_order', '-created_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_title', 'customer_location', 'customer_image')
        }),
        ('Testimonial Content', {
            'fields': ('testimonial_text', 'rating')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'sort_order')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'feature_type', 'is_active', 'sort_order']
    list_filter = ['feature_type', 'is_active']
    search_fields = ['name', 'short_description', 'detailed_description']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_description', 'detailed_description', 'icon', 'image')
        }),
        ('Feature Details', {
            'fields': ('feature_type', 'benefits')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'formatted_price', 'is_featured', 'is_active', 'sort_order']
    list_filter = ['is_featured', 'is_active', 'billing_period']
    search_fields = ['name', 'description']
    list_editable = ['is_featured', 'is_active', 'sort_order']
    ordering = ['sort_order', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'price', 'currency', 'billing_period', 'description')
        }),
        ('Plan Features', {
            'fields': ('features', 'limitations')
        }),
        ('Button Configuration', {
            'fields': ('button_text', 'button_url')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'sort_order')
        }),
    )
    
    def formatted_price(self, obj):
        return f"{obj.currency}{obj.price}/{obj.billing_period}"
    formatted_price.short_description = 'Price'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'sort_order']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'question']
    
    fieldsets = (
        ('FAQ Content', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_headquarters', 'phone', 'is_active', 'sort_order']
    list_filter = ['is_headquarters', 'is_active']
    search_fields = ['name', 'address', 'phone', 'email']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'phone', 'email', 'business_hours')
        }),
        ('Location Details', {
            'fields': ('latitude', 'longitude', 'google_maps_url'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_headquarters', 'is_active', 'sort_order')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['page', 'title', 'is_active']
    list_filter = ['page', 'is_active']
    search_fields = ['title', 'subtitle']
    
    fieldsets = (
        ('Page Information', {
            'fields': ('page', 'title', 'subtitle', 'background_image')
        }),
        ('Call-to-Action Buttons', {
            'fields': ('primary_button_text', 'primary_button_url', 'secondary_button_text', 'secondary_button_url'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'inquiry_type', 'is_read', 'is_resolved', 'created_at']
    list_filter = ['inquiry_type', 'is_read', 'is_resolved', 'newsletter_signup', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'company', 'message']
    list_editable = ['is_read', 'is_resolved']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'company')
        }),
        ('Inquiry Details', {
            'fields': ('inquiry_type', 'message', 'newsletter_signup')
        }),
        ('Status Management', {
            'fields': ('is_read', 'is_resolved', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')
    
    def has_add_permission(self, request):
        # Contact submissions are created through the form, not admin
        return False


# Custom admin site configuration
admin.site.site_header = "Gitako Administration"
admin.site.site_title = "Gitako Admin"
admin.site.index_title = "Agricultural Marketplace Management"