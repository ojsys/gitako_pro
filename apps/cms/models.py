from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class SiteSettings(models.Model):
    """Global site settings"""
    site_name = models.CharField(max_length=100, default="Gitako")
    tagline = models.CharField(max_length=200, default="Smart Farm Management for African Farmers")
    description = models.TextField(default="Transform your farming with digital tools")
    logo = models.ImageField(upload_to='cms/logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='cms/favicons/', blank=True, null=True)
    
    # Contact Information
    email = models.EmailField(default="hello@gitako.com")
    phone = models.CharField(max_length=30, default="+234 (0) 901 234 5678")
    address = models.TextField(default="Plot 123, Victoria Island, Lagos, Nigeria")
    
    # Social Media
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # Business Metrics
    active_farmers = models.PositiveIntegerField(default=1000)
    hectares_managed = models.PositiveIntegerField(default=5000)
    yield_increase_percentage = models.PositiveIntegerField(default=25)
    revenue_generated = models.CharField(max_length=20, default="₦2.5B")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.site_name} Settings"

    @classmethod
    def get_settings(cls):
        """Get the current site settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class TeamMember(models.Model):
    """Team members for the About page"""
    ROLE_CHOICES = [
        ('founder', 'Founder'),
        ('ceo', 'CEO'),
        ('cto', 'CTO'),
        ('head', 'Department Head'),
        ('manager', 'Manager'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='other')
    bio = models.TextField()
    image = models.ImageField(upload_to='cms/team/', blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.name} - {self.title}"


class Testimonial(models.Model):
    """Customer testimonials"""
    customer_name = models.CharField(max_length=100)
    customer_title = models.CharField(max_length=100)
    customer_location = models.CharField(max_length=100)
    customer_image = models.ImageField(upload_to='cms/testimonials/', blank=True, null=True)
    
    testimonial_text = models.TextField()
    rating = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.customer_name} - {self.customer_location}"


class Feature(models.Model):
    """Product features for Features page"""
    FEATURE_TYPE_CHOICES = [
        ('core', 'Core Feature'),
        ('advanced', 'Advanced Feature'),
        ('upcoming', 'Upcoming Feature'),
    ]

    name = models.CharField(max_length=100)
    short_description = models.CharField(max_length=200)
    detailed_description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Material icon name")
    image = models.ImageField(upload_to='cms/features/', blank=True, null=True)
    
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES, default='core')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Feature details
    benefits = models.JSONField(default=list, help_text="List of feature benefits")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Feature"
        verbose_name_plural = "Features"

    def __str__(self):
        return self.name


class PricingPlan(models.Model):
    """Pricing plans"""
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in Naira")
    currency = models.CharField(max_length=10, default="₦")
    billing_period = models.CharField(max_length=20, default="month")
    
    description = models.TextField()
    features = models.JSONField(default=list, help_text="List of plan features")
    limitations = models.JSONField(default=list, blank=True, help_text="List of plan limitations")
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Button customization
    button_text = models.CharField(max_length=50, default="Start Free Trial")
    button_url = models.CharField(max_length=200, default="/auth/register/")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'price']
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"

    def __str__(self):
        return f"{self.name} - {self.currency}{self.price}/{self.billing_period}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.CharField(max_length=50, default="General")
    
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Office(models.Model):
    """Office locations"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    
    # Business hours
    business_hours = models.CharField(max_length=100, default="Mon - Fri: 8:00 AM - 6:00 PM")
    
    # Map integration
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    google_maps_url = models.URLField(blank=True)
    
    is_headquarters = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Office"
        verbose_name_plural = "Offices"

    def __str__(self):
        return f"{self.name} {'(HQ)' if self.is_headquarters else ''}"


class HeroSection(models.Model):
    """Hero sections for different pages"""
    PAGE_CHOICES = [
        ('home', 'Homepage'),
        ('about', 'About'),
        ('features', 'Features'),
        ('pricing', 'Pricing'),
        ('contact', 'Contact'),
        ('offline', 'Offline'),
    ]

    page = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.TextField()
    background_image = models.ImageField(upload_to='cms/hero/', blank=True, null=True)
    
    # Call-to-action buttons
    primary_button_text = models.CharField(max_length=50, blank=True)
    primary_button_url = models.CharField(max_length=200, blank=True)
    secondary_button_text = models.CharField(max_length=50, blank=True)
    secondary_button_url = models.CharField(max_length=200, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"

    def __str__(self):
        return f"{self.get_page_display()} Hero"


class ContactSubmission(models.Model):
    """Contact form submissions"""
    INQUIRY_TYPE_CHOICES = [
        ('sales', 'Sales & Pricing'),
        ('support', 'Technical Support'),
        ('partnership', 'Partnership Opportunities'),
        ('feedback', 'Feedback & Suggestions'),
        ('demo', 'Request a Demo'),
        ('other', 'Other'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=100, blank=True)
    
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES)
    message = models.TextField()
    
    # Newsletter subscription
    newsletter_signup = models.BooleanField(default=False)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='assigned_contacts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_inquiry_type_display()}"