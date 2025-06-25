from django.contrib import admin
from .models import (
    SupplyCategory, Supply, StockMovement, Equipment, MaintenanceRecord,
    PurchaseOrder, PurchaseOrderItem
)


@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('movement_date', 'recorded_by')


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'current_stock', 'minimum_stock', 'unit_type', 'is_low_stock', 'is_active')
    list_filter = ('category', 'unit_type', 'is_active', 'expiry_tracking')
    search_fields = ('name', 'brand', 'model_number', 'supplier')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [StockMovementInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'brand', 'model_number')
        }),
        ('Stock Management', {
            'fields': ('unit_type', 'current_stock', 'minimum_stock', 'maximum_stock', 'unit_cost')
        }),
        ('Supplier Information', {
            'fields': ('supplier', 'supplier_contact')
        }),
        ('Storage & Tracking', {
            'fields': ('expiry_tracking', 'storage_location', 'storage_conditions')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('supply', 'movement_type', 'quantity', 'farm', 'movement_date', 'recorded_by')
    list_filter = ('movement_type', 'movement_date', 'farm')
    search_fields = ('supply__name', 'reference_number', 'supplier_vendor', 'batch_number')
    readonly_fields = ('movement_date', 'created_at')

    fieldsets = (
        ('Movement Details', {
            'fields': ('supply', 'movement_type', 'quantity', 'unit_cost')
        }),
        ('Reference Information', {
            'fields': ('reference_number', 'description', 'farm', 'supplier_vendor')
        }),
        ('Batch & Expiry', {
            'fields': ('expiry_date', 'batch_number')
        }),
        ('Tracking', {
            'fields': ('movement_date', 'recorded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )


class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'status', 'farm', 'assigned_to', 'is_maintenance_due', 'is_active')
    list_filter = ('equipment_type', 'status', 'farm', 'is_active')
    search_fields = ('name', 'brand', 'model', 'serial_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MaintenanceRecordInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'equipment_type', 'status', 'farm')
        }),
        ('Equipment Details', {
            'fields': ('brand', 'model', 'serial_number', 'location', 'assigned_to')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_cost', 'current_value', 'supplier', 'warranty_expiry')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance_date', 'next_maintenance_date', 'maintenance_interval_days')
        }),
        ('Operation', {
            'fields': ('operating_hours', 'fuel_type')
        }),
        ('Additional', {
            'fields': ('notes', 'image', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_maintenance_due(self, obj):
        return obj.is_maintenance_due
    is_maintenance_due.boolean = True
    is_maintenance_due.short_description = 'Maintenance Due'


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'maintenance_type', 'date_performed', 'performed_by', 'cost', 'recorded_by')
    list_filter = ('maintenance_type', 'date_performed', 'equipment__equipment_type')
    search_fields = ('equipment__name', 'performed_by', 'service_provider', 'invoice_number')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Maintenance Details', {
            'fields': ('equipment', 'maintenance_type', 'date_performed', 'description')
        }),
        ('Service Information', {
            'fields': ('performed_by', 'cost', 'service_provider', 'invoice_number')
        }),
        ('Parts & Next Maintenance', {
            'fields': ('parts_replaced', 'next_maintenance_due')
        }),
        ('Additional', {
            'fields': ('notes', 'recorded_by', 'created_at')
        }),
    )


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'order_date', 'total_amount', 'farm')
    list_filter = ('status', 'order_date', 'farm')
    search_fields = ('order_number', 'supplier', 'farm__name')
    readonly_fields = ('total_amount', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'farm', 'status')
        }),
        ('Supplier Details', {
            'fields': ('supplier', 'supplier_contact')
        }),
        ('Dates & Delivery', {
            'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Financial', {
            'fields': ('total_amount',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_conditions', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'supply', 'quantity', 'unit_price', 'total_price')
    list_filter = ('purchase_order__status', 'supply__category')
    search_fields = ('purchase_order__order_number', 'supply__name')
    readonly_fields = ('total_price',)