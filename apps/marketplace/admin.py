from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    ProductCategory, Product, ProductImage, Inquiry, Transaction, 
    Review, EscrowAccount, EscrowTransaction, MarketplaceSettings
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color_display', 'product_count', 'is_active', 'sort_order']
    list_filter = ['is_active', 'color']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'caption', 'sort_order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'seller', 'category', 'crop', 'status', 'featured',
        'quantity_available', 'price_per_unit', 'quality_grade',
        'view_count', 'inquiry_count', 'is_active_status', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'quality_grade', 'organic_certified',
        'delivery_available', 'featured', 'created_at'
    ]
    search_fields = ['title', 'description', 'seller__first_name', 'seller__last_name', 'crop__name']
    list_editable = ['status', 'featured']
    readonly_fields = ['view_count', 'inquiry_count', 'created_at', 'updated_at', 'is_active_status']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'crop', 'variety')
        }),
        ('Seller & Farm', {
            'fields': ('seller', 'farm')
        }),
        ('Product Details', {
            'fields': (
                'quantity_available', 'unit', 'price_per_unit', 'minimum_order',
                'quality_grade', 'organic_certified', 'certification_details'
            )
        }),
        ('Harvest & Processing', {
            'fields': ('harvest_date', 'processing_method', 'storage_conditions'),
            'classes': ('collapse',)
        }),
        ('Location & Logistics', {
            'fields': (
                'pickup_location', 'delivery_available', 
                'delivery_radius_km', 'delivery_cost_per_km'
            )
        }),
        ('Listing Management', {
            'fields': ('status', 'listing_expiry', 'featured', 'primary_image')
        }),
        ('Metrics', {
            'fields': ('view_count', 'inquiry_count', 'is_active_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;"> Active</span>')
        else:
            return format_html('<span style="color: red;"> Inactive</span>')
    is_active_status.short_description = 'Active Status'
    
    actions = ['make_featured', 'remove_featured', 'mark_as_sold']
    
    def make_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'{queryset.count()} products marked as featured.')
    make_featured.short_description = 'Mark selected products as featured'
    
    def remove_featured(self, request, queryset):
        queryset.update(featured=False)
        self.message_user(request, f'{queryset.count()} products removed from featured.')
    remove_featured.short_description = 'Remove featured status'
    
    def mark_as_sold(self, request, queryset):
        queryset.update(status=Product.ProductStatus.SOLD)
        self.message_user(request, f'{queryset.count()} products marked as sold.')
    mark_as_sold.short_description = 'Mark as sold'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'caption', 'sort_order', 'image_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__title', 'caption']
    list_editable = ['sort_order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'buyer', 'quantity_requested', 'offered_price_per_unit',
        'status', 'delivery_required', 'created_at'
    ]
    list_filter = ['status', 'delivery_required', 'created_at']
    search_fields = ['product__title', 'buyer__first_name', 'buyer__last_name', 'message']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    
    fieldsets = (
        ('Inquiry Details', {
            'fields': ('product', 'buyer', 'quantity_requested', 'offered_price_per_unit', 'message')
        }),
        ('Contact & Delivery', {
            'fields': (
                'buyer_contact', 'delivery_required', 
                'delivery_address', 'preferred_delivery_date'
            )
        }),
        ('Response', {
            'fields': ('status', 'seller_response', 'seller_responded_at')
        }),
        ('Summary', {
            'fields': ('total_amount',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_responded', 'mark_as_accepted', 'mark_as_declined']
    
    def mark_as_responded(self, request, queryset):
        queryset.update(status=Inquiry.InquiryStatus.RESPONDED, seller_responded_at=timezone.now())
        self.message_user(request, f'{queryset.count()} inquiries marked as responded.')
    mark_as_responded.short_description = 'Mark as responded'
    
    def mark_as_accepted(self, request, queryset):
        queryset.update(status=Inquiry.InquiryStatus.ACCEPTED)
        self.message_user(request, f'{queryset.count()} inquiries accepted.')
    mark_as_accepted.short_description = 'Accept inquiries'
    
    def mark_as_declined(self, request, queryset):
        queryset.update(status=Inquiry.InquiryStatus.DECLINED)
        self.message_user(request, f'{queryset.count()} inquiries declined.')
    mark_as_declined.short_description = 'Decline inquiries'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'product', 'buyer', 'seller', 'quantity',
        'total_amount', 'payment_method', 'status', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'delivery_required',
        'escrow_released', 'created_at'
    ]
    search_fields = [
        'reference_number', 'transaction_id', 'product__title',
        'buyer__first_name', 'seller__first_name'
    ]
    readonly_fields = [
        'transaction_id', 'reference_number', 'subtotal', 'platform_fee',
        'total_amount', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'transaction_id', 'reference_number', 'product', 'inquiry',
                'buyer', 'seller'
            )
        }),
        ('Order Details', {
            'fields': ('quantity', 'price_per_unit', 'subtotal', 'delivery_cost', 'platform_fee', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'payment_date')
        }),
        ('Escrow Information', {
            'fields': ('escrow_released', 'escrow_release_date', 'escrow_amount'),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_required', 'delivery_address', 'delivery_date', 'tracking_number'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Notes', {
            'fields': ('status', 'buyer_notes', 'seller_notes', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'release_escrow']
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status=Transaction.TransactionStatus.PAID, payment_date=timezone.now())
        self.message_user(request, f'{queryset.count()} transactions marked as paid.')
    mark_as_paid.short_description = 'Mark as paid'
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status=Transaction.TransactionStatus.SHIPPED)
        self.message_user(request, f'{queryset.count()} transactions marked as shipped.')
    mark_as_shipped.short_description = 'Mark as shipped'
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status=Transaction.TransactionStatus.DELIVERED)
        self.message_user(request, f'{queryset.count()} transactions marked as delivered.')
    mark_as_delivered.short_description = 'Mark as delivered'
    
    def release_escrow(self, request, queryset):
        released_count = 0
        for transaction in queryset:
            if transaction.release_escrow():
                released_count += 1
        self.message_user(request, f'{released_count} escrow payments released.')
    release_escrow.short_description = 'Release escrow payments'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'reviewer', 'reviewed_user', 'rating', 'title',
        'product_quality', 'communication', 'delivery_speed',
        'is_verified', 'helpful_votes', 'created_at'
    ]
    list_filter = ['rating', 'is_verified', 'created_at']
    search_fields = ['title', 'comment', 'reviewer__first_name', 'reviewed_user__first_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('transaction', 'reviewer', 'reviewed_user', 'rating', 'title', 'comment')
        }),
        ('Rating Breakdown', {
            'fields': ('product_quality', 'communication', 'delivery_speed'),
            'classes': ('collapse',)
        }),
        ('Verification & Engagement', {
            'fields': ('is_verified', 'helpful_votes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class EscrowTransactionInline(admin.TabularInline):
    model = EscrowTransaction
    extra = 0
    readonly_fields = ['created_at']
    fields = ['transaction_type', 'amount', 'reference', 'description', 'created_at']


@admin.register(EscrowAccount)
class EscrowAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_number', 'balance', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'account_number']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    inlines = [EscrowTransactionInline]
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_number', 'balance', 'status')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_name', 'bank_account_number'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'escrow_account', 'transaction_type', 'amount', 
        'reference', 'marketplace_transaction', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['reference', 'description', 'escrow_account__user__first_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'escrow_account', 'transaction_type', 'amount', 
                'reference', 'description', 'marketplace_transaction'
            )
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )


@admin.register(MarketplaceSettings)
class MarketplaceSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'platform_fee_percentage', 'escrow_hold_days', 'max_listing_days',
        'auto_extend_listings', 'require_verification', 'verification_threshold'
    ]
    
    fieldsets = (
        ('Fee Structure', {
            'fields': ('platform_fee_percentage',)
        }),
        ('Listing Settings', {
            'fields': ('max_listing_days', 'auto_extend_listings')
        }),
        ('Escrow Settings', {
            'fields': ('escrow_hold_days',)
        }),
        ('Verification Settings', {
            'fields': ('require_verification', 'verification_threshold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not MarketplaceSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


# Custom admin site configuration
admin.site.site_header = "Gitako Marketplace Administration"
admin.site.site_title = "Gitako Admin"
admin.site.index_title = "Marketplace Management"