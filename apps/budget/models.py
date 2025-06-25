from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True, help_text="Material icon name")
    color = models.CharField(max_length=7, default='#2e7d32', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'budget_budgetcategory'
        verbose_name = 'Budget Category'
        verbose_name_plural = 'Budget Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def full_name(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name


class Budget(models.Model):
    class BudgetType(models.TextChoices):
        SEASONAL = 'seasonal', 'Seasonal Budget'
        ANNUAL = 'annual', 'Annual Budget'
        PROJECT = 'project', 'Project Budget'
        BLOCK = 'block', 'Block Budget'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    budget_type = models.CharField(max_length=20, choices=BudgetType.choices, default=BudgetType.SEASONAL)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='budgets')
    block = models.ForeignKey('farms.Block', on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    calendar = models.ForeignKey('calendar.CropCalendar', on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_planned_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_planned_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_actual_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_actual_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    expected_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Expected yield in tons")
    expected_price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Expected price per unit (per kg/ton)")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_budgets')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_budget'
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} - {self.farm.name}"

    @property
    def planned_profit(self):
        return self.total_planned_income - self.total_planned_expenses

    @property
    def actual_profit(self):
        return self.total_actual_income - self.total_actual_expenses

    @property
    def profit_margin_planned(self):
        if self.total_planned_income > 0:
            return (self.planned_profit / self.total_planned_income) * 100
        return 0

    @property
    def profit_margin_actual(self):
        if self.total_actual_income > 0:
            return (self.actual_profit / self.total_actual_income) * 100
        return 0

    @property
    def expense_variance(self):
        return self.total_actual_expenses - self.total_planned_expenses

    @property
    def income_variance(self):
        return self.total_actual_income - self.total_planned_income

    @property
    def expense_variance_percentage(self):
        if self.total_planned_expenses > 0:
            return (self.expense_variance / self.total_planned_expenses) * 100
        return 0

    @property
    def budget_utilization(self):
        if self.total_planned_expenses > 0:
            return (self.total_actual_expenses / self.total_planned_expenses) * 100
        return 0

    def recalculate_totals(self):
        # Recalculate income totals
        income_data = self.income_items.aggregate(
            planned_total=models.Sum('planned_amount'),
            actual_total=models.Sum('actual_amount')
        )
        self.total_planned_income = income_data['planned_total'] or Decimal('0.00')
        self.total_actual_income = income_data['actual_total'] or Decimal('0.00')
        
        # Recalculate expense totals
        expense_data = self.expense_items.aggregate(
            planned_total=models.Sum('planned_amount'),
            actual_total=models.Sum('actual_amount')
        )
        self.total_planned_expenses = expense_data['planned_total'] or Decimal('0.00')
        self.total_actual_expenses = expense_data['actual_total'] or Decimal('0.00')
        
        self.save()


class BudgetItem(models.Model):
    class ItemType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=10, choices=ItemType.choices)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    planned_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    
    planned_quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True, help_text="e.g., kg, bags, liters, hours")
    
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    planned_date = models.DateField(null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)
    
    supplier_vendor = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    is_essential = models.BooleanField(default=True, help_text="Essential for farm operations")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_budgetitem'
        verbose_name = 'Budget Item'
        verbose_name_plural = 'Budget Items'
        ordering = ['planned_date', 'name']

    def __str__(self):
        return f"{self.name} - {self.budget.name}"

    @property
    def variance(self):
        return self.actual_amount - self.planned_amount

    @property
    def variance_percentage(self):
        if self.planned_amount > 0:
            return (self.variance / self.planned_amount) * 100
        return 0

    @property
    def is_over_budget(self):
        return self.actual_amount > self.planned_amount

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update budget totals when item is saved
        self.budget.recalculate_totals()


class IncomeItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='income_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    planned_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    
    planned_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Expected yield in tons/kg")
    actual_yield = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    planned_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Price per unit")
    actual_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    buyer = models.CharField(max_length=200, blank=True)
    sale_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_incomeitem'
        verbose_name = 'Income Item'
        verbose_name_plural = 'Income Items'
        ordering = ['sale_date', 'name']

    def __str__(self):
        return f"{self.name} - {self.budget.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.budget.recalculate_totals()


class ExpenseItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expense_items')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    planned_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    
    supplier = models.CharField(max_length=200, blank=True)
    expense_date = models.DateField(null=True, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_expenseitem'
        verbose_name = 'Expense Item'
        verbose_name_plural = 'Expense Items'
        ordering = ['expense_date', 'name']

    def __str__(self):
        return f"{self.name} - {self.budget.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.budget.recalculate_totals()


class BudgetTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    crop = models.ForeignKey('farms.Crop', on_delete=models.CASCADE, related_name='budget_templates')
    farm_size_hectares = models.DecimalField(max_digits=6, decimal_places=2, help_text="Template for how many hectares")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_budgettemplate'
        verbose_name = 'Budget Template'
        verbose_name_plural = 'Budget Templates'
        ordering = ['crop__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.crop.name} ({self.farm_size_hectares} ha)"


class BudgetTemplateItem(models.Model):
    template = models.ForeignKey(BudgetTemplate, on_delete=models.CASCADE, related_name='template_items')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=10, choices=BudgetItem.ItemType.choices)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount_per_hectare = models.DecimalField(max_digits=8, decimal_places=2)
    
    timing_days = models.PositiveIntegerField(help_text="Days from season start")
    is_essential = models.BooleanField(default=True)

    class Meta:
        db_table = 'budget_budgettemplateitem'
        verbose_name = 'Budget Template Item'
        verbose_name_plural = 'Budget Template Items'
        ordering = ['timing_days', 'name']

    def __str__(self):
        return f"{self.name} - {self.template.name}"