from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class SupplyCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Material icon name")
    color = models.CharField(max_length=7, default='#2196f3', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'inventory_supplycategory'
        verbose_name = 'Supply Category'
        verbose_name_plural = 'Supply Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Supply(models.Model):
    class UnitType(models.TextChoices):
        KILOGRAMS = 'kg', 'Kilograms'
        GRAMS = 'g', 'Grams'
        TONS = 't', 'Tons'
        LITERS = 'l', 'Liters'
        MILLILITERS = 'ml', 'Milliliters'
        PIECES = 'pcs', 'Pieces'
        BAGS = 'bags', 'Bags'
        BOTTLES = 'bottles', 'Bottles'
        BOXES = 'boxes', 'Boxes'
        PACKETS = 'packets', 'Packets'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(SupplyCategory, on_delete=models.CASCADE, related_name='supplies')
    brand = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.KILOGRAMS)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    supplier_contact = models.CharField(max_length=200, blank=True)
    
    expiry_tracking = models.BooleanField(default=False, help_text="Track expiry dates for this supply")
    storage_location = models.CharField(max_length=200, blank=True)
    storage_conditions = models.TextField(blank=True, help_text="Special storage requirements")
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory_supply'
        verbose_name = 'Supply'
        verbose_name_plural = 'Supplies'
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit_type})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

    @property
    def stock_percentage(self):
        if self.maximum_stock and self.maximum_stock > 0:
            return (self.current_stock / self.maximum_stock) * 100
        return 0

    @property
    def total_value(self):
        if self.unit_cost:
            return self.current_stock * self.unit_cost
        return Decimal('0.00')


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        TRANSFER = 'transfer', 'Transfer'
        WASTE = 'waste', 'Waste/Loss'

    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=15, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    reference_number = models.CharField(max_length=100, blank=True, help_text="Purchase order, invoice number, etc.")
    description = models.TextField(blank=True)
    
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='stock_movements')
    supplier_vendor = models.CharField(max_length=200, blank=True)
    
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    
    movement_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_stockmovement'
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.supply.name} ({self.quantity} {self.supply.unit_type})"

    def save(self, *args, **kwargs):
        # Update supply stock levels
        if self.pk is None:  # New record
            if self.movement_type == self.MovementType.IN:
                self.supply.current_stock += self.quantity
            elif self.movement_type in [self.MovementType.OUT, self.MovementType.WASTE]:
                self.supply.current_stock -= self.quantity
            elif self.movement_type == self.MovementType.ADJUSTMENT:
                # For adjustments, quantity represents the new total, not the change
                self.supply.current_stock = self.quantity
                
            self.supply.save()
        
        super().save(*args, **kwargs)


class Equipment(models.Model):
    class EquipmentType(models.TextChoices):
        MACHINERY = 'machinery', 'Machinery'
        TOOLS = 'tools', 'Tools'
        VEHICLES = 'vehicles', 'Vehicles'
        IRRIGATION = 'irrigation', 'Irrigation Equipment'
        PROCESSING = 'processing', 'Processing Equipment'
        STORAGE = 'storage', 'Storage Equipment'
        SAFETY = 'safety', 'Safety Equipment'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPERATIONAL = 'operational', 'Operational'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        REPAIR = 'repair', 'Needs Repair'
        OUT_OF_SERVICE = 'out_of_service', 'Out of Service'
        RETIRED = 'retired', 'Retired'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    equipment_type = models.CharField(max_length=20, choices=EquipmentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPERATIONAL)
    
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='equipment')
    
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    supplier = models.CharField(max_length=200, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    location = models.CharField(max_length=200, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_equipment'
    )
    
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_interval_days = models.PositiveIntegerField(null=True, blank=True)
    
    operating_hours = models.DecimalField(max_digits=8, decimal_places=1, default=Decimal('0.0'))
    fuel_type = models.CharField(max_length=50, blank=True)
    
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='equipment/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory_equipment'
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
        ordering = ['equipment_type', 'name']

    def __str__(self):
        return f"{self.name} - {self.farm.name}"

    @property
    def is_maintenance_due(self):
        if self.next_maintenance_date:
            return timezone.now().date() >= self.next_maintenance_date
        return False

    @property
    def days_to_maintenance(self):
        if self.next_maintenance_date:
            return (self.next_maintenance_date - timezone.now().date()).days
        return None

    @property
    def is_under_warranty(self):
        if self.warranty_expiry:
            return timezone.now().date() <= self.warranty_expiry
        return False


class MaintenanceRecord(models.Model):
    class MaintenanceType(models.TextChoices):
        ROUTINE = 'routine', 'Routine Maintenance'
        REPAIR = 'repair', 'Repair'
        INSPECTION = 'inspection', 'Inspection'
        UPGRADE = 'upgrade', 'Upgrade'
        EMERGENCY = 'emergency', 'Emergency Repair'

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=15, choices=MaintenanceType.choices)
    
    date_performed = models.DateField()
    description = models.TextField()
    
    performed_by = models.CharField(max_length=200, help_text="Technician or service provider")
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    parts_replaced = models.TextField(blank=True)
    next_maintenance_due = models.DateField(null=True, blank=True)
    
    service_provider = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_maintenancerecord'
        verbose_name = 'Maintenance Record'
        verbose_name_plural = 'Maintenance Records'
        ordering = ['-date_performed']

    def __str__(self):
        return f"{self.equipment.name} - {self.get_maintenance_type_display()} ({self.date_performed})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update equipment's last maintenance date
        self.equipment.last_maintenance_date = self.date_performed
        if self.next_maintenance_due:
            self.equipment.next_maintenance_date = self.next_maintenance_due
        self.equipment.save()


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        CONFIRMED = 'confirmed', 'Confirmed'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    order_number = models.CharField(max_length=100, unique=True)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.CharField(max_length=200)
    supplier_contact = models.TextField(blank=True)
    
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory_purchaseorder'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date']

    def __str__(self):
        return f"PO {self.order_number} - {self.supplier}"

    def calculate_total(self):
        total = self.items.aggregate(total=models.Sum(
            models.F('quantity') * models.F('unit_price'),
            output_field=models.DecimalField()
        ))['total'] or Decimal('0.00')
        self.total_amount = total
        self.save()


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_purchaseorderitem'
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'

    def __str__(self):
        return f"{self.supply.name} - {self.quantity} {self.supply.unit_type}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_order.calculate_total()