from django.contrib import admin
from .models import (
    BudgetCategory, Budget, BudgetItem, IncomeItem, ExpenseItem,
    BudgetTemplate, BudgetTemplateItem
)


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'icon', 'color', 'is_active', 'sort_order')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')


class IncomeItemInline(admin.TabularInline):
    model = IncomeItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class ExpenseItemInline(admin.TabularInline):
    model = ExpenseItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class BudgetItemInline(admin.TabularInline):
    model = BudgetItem
    extra = 0
    readonly_fields = ('variance', 'variance_percentage', 'created_at', 'updated_at')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget_type', 'status', 'farm', 'start_date', 'end_date', 'planned_profit', 'actual_profit')
    list_filter = ('budget_type', 'status', 'farm', 'start_date')
    search_fields = ('name', 'description', 'farm__name')
    readonly_fields = ('total_planned_income', 'total_planned_expenses', 'total_actual_income', 'total_actual_expenses', 'created_at', 'updated_at')
    inlines = [IncomeItemInline, ExpenseItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'budget_type', 'status')
        }),
        ('Farm & Calendar', {
            'fields': ('farm', 'block', 'calendar')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Totals (Auto-calculated)', {
            'fields': ('total_planned_income', 'total_planned_expenses', 'total_actual_income', 'total_actual_expenses'),
            'classes': ('collapse',)
        }),
        ('Yield Expectations', {
            'fields': ('expected_yield', 'expected_price_per_unit')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def planned_profit(self, obj):
        return obj.planned_profit
    planned_profit.short_description = 'Planned Profit'

    def actual_profit(self, obj):
        return obj.actual_profit
    actual_profit.short_description = 'Actual Profit'


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'item_type', 'category', 'planned_amount', 'actual_amount', 'variance', 'is_over_budget')
    list_filter = ('item_type', 'category', 'is_recurring', 'is_essential', 'budget__status')
    search_fields = ('name', 'description', 'budget__name', 'supplier_vendor')
    readonly_fields = ('variance', 'variance_percentage', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('budget', 'category', 'item_type', 'name', 'description')
        }),
        ('Financial', {
            'fields': ('planned_amount', 'actual_amount', 'planned_quantity', 'actual_quantity', 'unit', 'unit_price')
        }),
        ('Dates', {
            'fields': ('planned_date', 'actual_date')
        }),
        ('Supplier & Payment', {
            'fields': ('supplier_vendor', 'payment_method', 'receipt_number')
        }),
        ('Properties', {
            'fields': ('is_recurring', 'is_essential', 'notes')
        }),
        ('Calculations', {
            'fields': ('variance', 'variance_percentage'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def variance(self, obj):
        return obj.variance
    variance.short_description = 'Variance'

    def is_over_budget(self, obj):
        return obj.is_over_budget
    is_over_budget.boolean = True
    is_over_budget.short_description = 'Over Budget'


@admin.register(IncomeItem)
class IncomeItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'planned_amount', 'actual_amount', 'planned_yield', 'actual_yield', 'buyer', 'sale_date')
    list_filter = ('sale_date', 'budget__status', 'budget__farm')
    search_fields = ('name', 'description', 'budget__name', 'buyer')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('budget', 'name', 'description')
        }),
        ('Financial', {
            'fields': ('planned_amount', 'actual_amount', 'planned_price', 'actual_price')
        }),
        ('Yield', {
            'fields': ('planned_yield', 'actual_yield')
        }),
        ('Sale Information', {
            'fields': ('buyer', 'sale_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'category', 'planned_amount', 'actual_amount', 'supplier', 'expense_date')
    list_filter = ('category', 'expense_date', 'budget__status', 'budget__farm')
    search_fields = ('name', 'description', 'budget__name', 'supplier', 'receipt_number')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('budget', 'category', 'name', 'description')
        }),
        ('Financial', {
            'fields': ('planned_amount', 'actual_amount')
        }),
        ('Purchase Information', {
            'fields': ('supplier', 'expense_date', 'receipt_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class BudgetTemplateItemInline(admin.TabularInline):
    model = BudgetTemplateItem
    extra = 0


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'crop', 'farm_size_hectares', 'is_public', 'created_by')
    list_filter = ('crop', 'is_public', 'created_by')
    search_fields = ('name', 'description', 'crop__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BudgetTemplateItemInline]

    fieldsets = (
        ('Template Details', {
            'fields': ('name', 'description', 'crop', 'farm_size_hectares')
        }),
        ('Access Control', {
            'fields': ('created_by', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetTemplateItem)
class BudgetTemplateItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'category', 'item_type', 'amount_per_hectare', 'timing_days', 'is_essential')
    list_filter = ('item_type', 'category', 'is_essential', 'template__crop')
    search_fields = ('name', 'description', 'template__name', 'template__crop__name')

    fieldsets = (
        ('Template Item Details', {
            'fields': ('template', 'category', 'item_type', 'name', 'description')
        }),
        ('Financial & Timing', {
            'fields': ('amount_per_hectare', 'timing_days', 'is_essential')
        }),
    )