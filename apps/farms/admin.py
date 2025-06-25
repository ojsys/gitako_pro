from django.contrib import admin
from .models import Farm, Crop, CropVariety, Block, FarmStaff, FarmerRecord


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'total_area', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'owner__role')
    search_fields = ('name', 'owner__email', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'maturity_days', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'scientific_name')


@admin.register(CropVariety)
class CropVarietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'crop', 'maturity_days', 'yield_per_hectare', 'is_active')
    list_filter = ('crop', 'is_active')
    search_fields = ('name', 'crop__name')


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'size', 'crop', 'variety', 'block_manager', 'is_active')
    list_filter = ('is_active', 'crop', 'farm')
    search_fields = ('name', 'farm__name', 'crop__name')


@admin.register(FarmStaff)
class FarmStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'farm', 'role', 'hire_date', 'is_active')
    list_filter = ('role', 'is_active', 'hire_date')
    search_fields = ('user__email', 'farm__name')


@admin.register(FarmerRecord)
class FarmerRecordAdmin(admin.ModelAdmin):
    list_display = ('farmer_name', 'farm', 'allocated_hectares', 'season_year', 'is_active')
    list_filter = ('season_year', 'is_active', 'farm')
    search_fields = ('farmer_name', 'farmer_email', 'location')