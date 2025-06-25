from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Material icon name")
    color = models.CharField(max_length=7, default='#4caf50', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'marketplace_productcategory'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        SOLD = 'sold', 'Sold'
        EXPIRED = 'expired', 'Expired'
        SUSPENDED = 'suspended', 'Suspended'

    class QualityGrade(models.TextChoices):
        GRADE_A = 'grade_a', 'Grade A (Premium)'
        GRADE_B = 'grade_b', 'Grade B (Standard)'
        GRADE_C = 'grade_c', 'Grade C (Commercial)'
        MIXED = 'mixed', 'Mixed Grade'

    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    crop = models.ForeignKey('farms.Crop', on_delete=models.CASCADE, related_name='marketplace_products')
    variety = models.ForeignKey('farms.CropVariety', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Seller Information
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='marketplace_products')
    
    # Product Details
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, default='kg', help_text="e.g., kg, tons, bags, pieces")
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    
    # Quality & Certification
    quality_grade = models.CharField(max_length=10, choices=QualityGrade.choices, default=QualityGrade.GRADE_B)
    organic_certified = models.BooleanField(default=False)
    certification_details = models.TextField(blank=True)
    
    # Harvest & Processing
    harvest_date = models.DateField(null=True, blank=True)
    processing_method = models.CharField(max_length=200, blank=True)
    storage_conditions = models.TextField(blank=True)
    
    # Location & Logistics
    pickup_location = models.CharField(max_length=300)
    delivery_available = models.BooleanField(default=False)
    delivery_radius_km = models.PositiveIntegerField(null=True, blank=True)
    delivery_cost_per_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Listing Details
    status = models.CharField(max_length=15, choices=ProductStatus.choices, default=ProductStatus.DRAFT)
    listing_expiry = models.DateTimeField(help_text="When this listing expires")
    featured = models.BooleanField(default=False)
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    inquiry_count = models.PositiveIntegerField(default=0)
    
    # Media
    primary_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.seller.full_name}"

    @property
    def is_active(self):
        return (
            self.status == self.ProductStatus.ACTIVE and
            self.listing_expiry > timezone.now() and
            self.quantity_available > 0
        )

    @property
    def is_expired(self):
        return timezone.now() > self.listing_expiry

    @property
    def total_value(self):
        return self.quantity_available * self.price_per_unit

    @property
    def days_until_expiry(self):
        if self.listing_expiry:
            delta = self.listing_expiry - timezone.now()
            return delta.days if delta.days > 0 else 0
        return 0

    def increment_views(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_inquiries(self):
        self.inquiry_count += 1
        self.save(update_fields=['inquiry_count'])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketplace_productimage'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.title} - Image {self.sort_order}"


class Inquiry(models.Model):
    class InquiryStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RESPONDED = 'responded', 'Responded'
        NEGOTIATING = 'negotiating', 'Negotiating'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inquiries')
    
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)
    offered_price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    message = models.TextField()
    
    buyer_contact = models.CharField(max_length=200, blank=True)
    delivery_required = models.BooleanField(default=False)
    delivery_address = models.TextField(blank=True)
    preferred_delivery_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=15, choices=InquiryStatus.choices, default=InquiryStatus.PENDING)
    seller_response = models.TextField(blank=True)
    seller_responded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_inquiry'
        verbose_name = 'Inquiry'
        verbose_name_plural = 'Inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry for {self.product.title} by {self.buyer.full_name}"

    @property
    def total_amount(self):
        price = self.offered_price_per_unit or self.product.price_per_unit
        return self.quantity_requested * price


class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Payment'
        PAID = 'paid', 'Payment Received'
        IN_ESCROW = 'in_escrow', 'In Escrow'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
        DISPUTED = 'disputed', 'Disputed'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CARD = 'card', 'Credit/Debit Card'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        CRYPTO = 'crypto', 'Cryptocurrency'
        CASH_ON_DELIVERY = 'cod', 'Cash on Delivery'

    # Transaction Identification
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference_number = models.CharField(max_length=50, unique=True)
    
    # Parties
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')
    inquiry = models.OneToOneField(Inquiry, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transaction Details
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Escrow Information
    escrow_released = models.BooleanField(default=False)
    escrow_release_date = models.DateTimeField(null=True, blank=True)
    escrow_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Delivery Information
    delivery_required = models.BooleanField(default=False)
    delivery_address = models.TextField(blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Status & Timestamps
    status = models.CharField(max_length=15, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    status_updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    buyer_notes = models.TextField(blank=True)
    seller_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_transaction'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.reference_number} - {self.product.title}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"GT{timezone.now().strftime('%Y%m%d')}{str(self.transaction_id)[:8].upper()}"
        
        # Calculate totals
        self.subtotal = self.quantity * self.price_per_unit
        
        # Calculate platform fee (2.5% of subtotal)
        self.platform_fee = self.subtotal * Decimal('0.025')
        
        # Calculate total
        self.total_amount = self.subtotal + self.delivery_cost + self.platform_fee
        
        super().save(*args, **kwargs)

    def release_escrow(self):
        """Release escrowed funds to seller"""
        if self.status == self.TransactionStatus.IN_ESCROW:
            self.escrow_released = True
            self.escrow_release_date = timezone.now()
            self.status = self.TransactionStatus.COMPLETED
            self.save()
            
            # Here you would integrate with actual payment processor
            # to transfer funds from escrow to seller
            
            return True
        return False

    def initiate_refund(self):
        """Initiate refund process"""
        if self.status in [self.TransactionStatus.PAID, self.TransactionStatus.IN_ESCROW]:
            self.status = self.TransactionStatus.REFUNDED
            self.save()
            
            # Here you would integrate with payment processor
            # to process the refund
            
            return True
        return False


class Review(models.Model):
    class Rating(models.IntegerChoices):
        ONE = 1, '1 Star'
        TWO = 2, '2 Stars'
        THREE = 3, '3 Stars'
        FOUR = 4, '4 Stars'
        FIVE = 5, '5 Stars'

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Rating Categories
    product_quality = models.PositiveSmallIntegerField(choices=Rating.choices, null=True, blank=True)
    communication = models.PositiveSmallIntegerField(choices=Rating.choices, null=True, blank=True)
    delivery_speed = models.PositiveSmallIntegerField(choices=Rating.choices, null=True, blank=True)
    
    is_verified = models.BooleanField(default=True)  # Based on completed transaction
    helpful_votes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_review'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['transaction', 'reviewer']

    def __str__(self):
        return f"Review by {self.reviewer.full_name} for {self.reviewed_user.full_name}"


class EscrowAccount(models.Model):
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        CLOSED = 'closed', 'Closed'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_account')
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Bank details for withdrawals
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    
    status = models.CharField(max_length=15, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_escrowaccount'
        verbose_name = 'Escrow Account'
        verbose_name_plural = 'Escrow Accounts'

    def __str__(self):
        return f"Escrow Account - {self.user.full_name} ({self.account_number})"

    def save(self, *args, **kwargs):
        if not self.account_number:
            # Generate unique account number
            import random
            self.account_number = f"ESC{random.randint(1000000, 9999999)}"
        super().save(*args, **kwargs)


class EscrowTransaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        HOLD = 'hold', 'Hold'
        RELEASE = 'release', 'Release'
        REFUND = 'refund', 'Refund'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        FEE = 'fee', 'Fee'

    escrow_account = models.ForeignKey(EscrowAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=15, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=200)
    description = models.TextField()
    
    marketplace_transaction = models.ForeignKey(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='escrow_transactions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'marketplace_escrowtransaction'
        verbose_name = 'Escrow Transaction'
        verbose_name_plural = 'Escrow Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} ({self.escrow_account.user.full_name})"


class MarketplaceSettings(models.Model):
    platform_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('2.50'),
        help_text="Platform fee as percentage of transaction value"
    )
    escrow_hold_days = models.PositiveIntegerField(
        default=7,
        help_text="Days to hold payment in escrow after delivery"
    )
    max_listing_days = models.PositiveIntegerField(
        default=30,
        help_text="Maximum days a product can be listed"
    )
    auto_extend_listings = models.BooleanField(
        default=True,
        help_text="Automatically extend listings before expiry"
    )
    require_verification = models.BooleanField(
        default=False,
        help_text="Require user verification for high-value transactions"
    )
    verification_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100000.00'),
        help_text="Amount above which verification is required"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_settings'
        verbose_name = 'Marketplace Settings'
        verbose_name_plural = 'Marketplace Settings'

    def __str__(self):
        return f"Marketplace Settings (Fee: {self.platform_fee_percentage}%)"

    @classmethod
    def get_settings(cls):
        """Get the current marketplace settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings