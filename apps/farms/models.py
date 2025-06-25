from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Farm(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_farms')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='farms')
    total_area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total farm area in hectares")
    location = models.CharField(max_length=300, help_text="Farm location/address")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    soil_type = models.CharField(max_length=100, blank=True)
    climate_zone = models.CharField(max_length=100, blank=True)
    water_source = models.CharField(max_length=200, blank=True)
    farm_image = models.ImageField(upload_to='farm_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_farm'
        verbose_name = 'Farm'
        verbose_name_plural = 'Farms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.total_area} ha)"

    @property
    def total_blocks(self):
        return self.blocks.count()

    @property
    def total_allocated_area(self):
        return self.blocks.aggregate(total=models.Sum('size'))['total'] or Decimal('0')

    @property
    def available_area(self):
        return self.total_area - self.total_allocated_area


class Crop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    scientific_name = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=50, help_text="e.g., Cereal, Legume, Vegetable, etc.")
    growing_season = models.CharField(max_length=100, help_text="e.g., Rainy season, Dry season, All year")
    maturity_days = models.PositiveIntegerField(help_text="Days to maturity")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='crop_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_crop'
        verbose_name = 'Crop'
        verbose_name_plural = 'Crops'
        ordering = ['name']

    def __str__(self):
        return self.name


class CropVariety(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='varieties')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    maturity_days = models.PositiveIntegerField(help_text="Days to maturity for this variety")
    yield_per_hectare = models.DecimalField(max_digits=8, decimal_places=2, help_text="Expected yield per hectare")
    resistance_traits = models.TextField(blank=True, help_text="Disease/pest resistance traits")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_cropvariety'
        verbose_name = 'Crop Variety'
        verbose_name_plural = 'Crop Varieties'
        unique_together = ['crop', 'name']
        ordering = ['crop__name', 'name']

    def __str__(self):
        return f"{self.crop.name} - {self.name}"


class Block(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='blocks')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    size = models.DecimalField(max_digits=8, decimal_places=2, help_text="Block size in hectares")
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True)
    variety = models.ForeignKey(CropVariety, on_delete=models.SET_NULL, null=True, blank=True)
    plant_population = models.PositiveIntegerField(null=True, blank=True, help_text="Number of plants per hectare")
    expected_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Expected yield in tons")
    actual_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Actual yield achieved")
    block_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_blocks')
    soil_ph = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(14)])
    irrigation_type = models.CharField(max_length=100, blank=True)
    planting_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    actual_harvest_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_block'
        verbose_name = 'Block/Field'
        verbose_name_plural = 'Blocks/Fields'
        ordering = ['farm__name', 'name']

    def __str__(self):
        return f"{self.farm.name} - {self.name}"

    @property
    def growth_stage(self):
        if not self.planting_date:
            return "Not Planted"
        elif not self.actual_harvest_date:
            return "Growing"
        else:
            return "Harvested"


class FarmStaff(models.Model):
    class StaffRole(models.TextChoices):
        MANAGER = 'manager', 'Farm Manager'
        SUPERVISOR = 'supervisor', 'Supervisor'
        FIELD_WORKER = 'field_worker', 'Field Worker'
        TECHNICIAN = 'technician', 'Technician'
        SECURITY = 'security', 'Security'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='staff')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farm_assignments')
    role = models.CharField(max_length=20, choices=StaffRole.choices)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_farmstaff'
        verbose_name = 'Farm Staff'
        verbose_name_plural = 'Farm Staff'
        unique_together = ['farm', 'user']
        ordering = ['farm__name', 'user__first_name']

    def __str__(self):
        return f"{self.user.full_name} - {self.farm.name} ({self.role})"


class FieldTask(models.Model):
    class TaskType(models.TextChoices):
        PLANTING = 'planting', 'Planting'
        WATERING = 'watering', 'Watering'
        FERTILIZING = 'fertilizing', 'Fertilizing'
        WEEDING = 'weeding', 'Weeding'
        PEST_CONTROL = 'pest_control', 'Pest Control'
        HARVESTING = 'harvesting', 'Harvesting'
        SOIL_PREPARATION = 'soil_prep', 'Soil Preparation'
        INSPECTION = 'inspection', 'Field Inspection'
        MAINTENANCE = 'maintenance', 'Equipment Maintenance'
        OTHER = 'other', 'Other'
    
    class TaskStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='tasks')
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    
    due_date = models.DateTimeField()
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_fieldtask'
        verbose_name = 'Field Task'
        verbose_name_plural = 'Field Tasks'
        ordering = ['-due_date', '-priority']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.full_name}"


class FieldInventory(models.Model):
    class ItemType(models.TextChoices):
        SEEDS = 'seeds', 'Seeds'
        FERTILIZER = 'fertilizer', 'Fertilizer'
        PESTICIDE = 'pesticide', 'Pesticide'
        TOOLS = 'tools', 'Tools'
        EQUIPMENT = 'equipment', 'Equipment'
        SUPPLIES = 'supplies', 'General Supplies'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='inventory')
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    
    item_name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    description = models.TextField(blank=True)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g., kg, liters, pieces")
    
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    location = models.CharField(max_length=200, blank=True, help_text="Storage location")
    expiry_date = models.DateField(null=True, blank=True)
    
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory_records')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_fieldinventory'
        verbose_name = 'Field Inventory'
        verbose_name_plural = 'Field Inventory'
        ordering = ['item_name']

    def __str__(self):
        return f"{self.item_name} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date <= timezone.now().date()
        return False


class FarmerRecord(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='farmer_records')
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='farmer_records', null=True, blank=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True, blank=True)
    farmer_name = models.CharField(max_length=200)
    farmer_email = models.EmailField(blank=True)
    farmer_phone = models.CharField(max_length=17, blank=True)
    location = models.CharField(max_length=300, blank=True)
    allocated_hectares = models.DecimalField(max_digits=8, decimal_places=2)
    crops_grown = models.ManyToManyField(Crop, blank=True)
    season_year = models.PositiveIntegerField()
    expected_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Additional farmer information
    farming_experience = models.PositiveIntegerField(null=True, blank=True, help_text="Years of farming experience")
    irrigation_method = models.CharField(max_length=100, blank=True, help_text="Type of irrigation used")
    soil_type = models.CharField(max_length=100, blank=True, help_text="Soil type on farmer's land")
    registration_date = models.DateField(null=True, blank=True, help_text="Date farmer joined the program")
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms_farmerrecord'
        verbose_name = 'Farmer Record'
        verbose_name_plural = 'Farmer Records'
        ordering = ['-season_year', 'farmer_name']

    def __str__(self):
        return f"{self.farmer_name} - {self.allocated_hectares} ha ({self.season_year})"

    @property
    def yield_efficiency(self):
        if self.expected_yield and self.actual_yield:
            return (self.actual_yield / self.expected_yield) * 100
        return None