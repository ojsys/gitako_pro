from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

from apps.marketplace.models import ProductCategory, Product
from apps.farms.models import Farm, Crop, CropVariety

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample marketplace data for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=int,
            default=20,
            help='Number of sample products to create (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating sample marketplace data...')
        
        # Create product categories
        self.create_categories()
        
        # Create sample users and farms if they don't exist
        self.create_sample_users()
        
        # Create sample products
        num_products = options['products']
        self.create_sample_products(num_products)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample marketplace data with {num_products} products!'
            )
        )

    def create_categories(self):
        """Create product categories"""
        categories_data = [
            {'name': 'Fruits', 'description': 'Fresh fruits and citrus', 'icon': 'apple', 'color': '#ff5722'},
            {'name': 'Vegetables', 'description': 'Fresh vegetables and greens', 'icon': 'eco', 'color': '#4caf50'},
            {'name': 'Grains & Cereals', 'description': 'Rice, corn, wheat and other grains', 'icon': 'grain', 'color': '#ff9800'},
            {'name': 'Legumes', 'description': 'Beans, peas, lentils and pulses', 'icon': 'scatter_plot', 'color': '#8bc34a'},
            {'name': 'Tubers', 'description': 'Potatoes, yams, cassava and root vegetables', 'icon': 'landscape', 'color': '#795548'},
            {'name': 'Herbs & Spices', 'description': 'Fresh and dried herbs, spices', 'icon': 'local_florist', 'color': '#009688'},
            {'name': 'Nuts & Seeds', 'description': 'Tree nuts, seeds and oilseeds', 'icon': 'circle', 'color': '#607d8b'},
            {'name': 'Livestock Products', 'description': 'Eggs, dairy and meat products', 'icon': 'pets', 'color': '#9c27b0'},
        ]
        
        created_count = 0
        for cat_data in categories_data:
            category, created = ProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_active': True,
                    'sort_order': created_count
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created category: {category.name}')
        
        self.stdout.write(f'Categories ready: {ProductCategory.objects.count()} total')

    def create_sample_users(self):
        """Create sample users and farms if they don't exist"""
        sample_users_data = [
            {
                'username': 'john_farmer',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Okafor',
                'farm_name': 'Green Valley Farm',
                'location': 'Abuja, Nigeria'
            },
            {
                'username': 'mary_agric',
                'email': 'mary@example.com',
                'first_name': 'Mary',
                'last_name': 'Adebayo',
                'farm_name': 'Sunshine Agricultural Enterprise',
                'location': 'Lagos, Nigeria'
            },
            {
                'username': 'david_crops',
                'email': 'david@example.com',
                'first_name': 'David',
                'last_name': 'Musa',
                'farm_name': 'Northern Harvest Farm',
                'location': 'Kano, Nigeria'
            },
            {
                'username': 'sarah_organic',
                'email': 'sarah@example.com',
                'first_name': 'Sarah',
                'last_name': 'Eze',
                'farm_name': 'Organic Gardens Ltd',
                'location': 'Enugu, Nigeria'
            },
            {
                'username': 'ahmed_produce',
                'email': 'ahmed@example.com',
                'first_name': 'Ahmed',
                'last_name': 'Bello',
                'farm_name': 'Desert Bloom Farm',
                'location': 'Sokoto, Nigeria'
            }
        ]
        
        for user_data in sample_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            
            if created:
                user.set_password('password123')  # Default password
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            
            # Create farm for user
            farm, farm_created = Farm.objects.get_or_create(
                owner=user,
                name=user_data['farm_name'],
                defaults={
                    'location': user_data['location'],
                    'total_area': Decimal(str(random.randint(10, 200))),
                    'description': f'A productive farm in {user_data["location"]} specializing in various crops.',
                    'is_active': True
                }
            )
            
            if farm_created:
                self.stdout.write(f'Created farm: {farm.name}')

        self.stdout.write(f'Sample users ready: {User.objects.count()} total users')

    def create_sample_products(self, num_products):
        """Create sample products"""
        
        # Sample product data templates
        product_templates = [
            # Fruits
            {'title': 'Fresh Oranges', 'category': 'Fruits', 'crop': 'Orange', 'unit': 'kg', 'min_price': 200, 'max_price': 500},
            {'title': 'Ripe Bananas', 'category': 'Fruits', 'crop': 'Banana', 'unit': 'bunch', 'min_price': 150, 'max_price': 400},
            {'title': 'Sweet Pineapples', 'category': 'Fruits', 'crop': 'Pineapple', 'unit': 'piece', 'min_price': 300, 'max_price': 800},
            {'title': 'Fresh Mangoes', 'category': 'Fruits', 'crop': 'Mango', 'unit': 'kg', 'min_price': 250, 'max_price': 600},
            {'title': 'Watermelons', 'category': 'Fruits', 'crop': 'Watermelon', 'unit': 'piece', 'min_price': 500, 'max_price': 1500},
            
            # Vegetables
            {'title': 'Fresh Tomatoes', 'category': 'Vegetables', 'crop': 'Tomato', 'unit': 'kg', 'min_price': 150, 'max_price': 400},
            {'title': 'Green Pepper', 'category': 'Vegetables', 'crop': 'Pepper', 'unit': 'kg', 'min_price': 200, 'max_price': 500},
            {'title': 'Fresh Onions', 'category': 'Vegetables', 'crop': 'Onion', 'unit': 'kg', 'min_price': 180, 'max_price': 450},
            {'title': 'Leafy Spinach', 'category': 'Vegetables', 'crop': 'Spinach', 'unit': 'bundle', 'min_price': 100, 'max_price': 250},
            {'title': 'Cucumber', 'category': 'Vegetables', 'crop': 'Cucumber', 'unit': 'kg', 'min_price': 120, 'max_price': 300},
            
            # Grains
            {'title': 'Premium Rice', 'category': 'Grains & Cereals', 'crop': 'Rice', 'unit': 'bag', 'min_price': 15000, 'max_price': 25000},
            {'title': 'Yellow Corn', 'category': 'Grains & Cereals', 'crop': 'Corn', 'unit': 'bag', 'min_price': 12000, 'max_price': 20000},
            {'title': 'Wheat Grain', 'category': 'Grains & Cereals', 'crop': 'Wheat', 'unit': 'bag', 'min_price': 18000, 'max_price': 28000},
            
            # Legumes
            {'title': 'Black-eyed Beans', 'category': 'Legumes', 'crop': 'Beans', 'unit': 'kg', 'min_price': 400, 'max_price': 800},
            {'title': 'Groundnuts', 'category': 'Nuts & Seeds', 'crop': 'Groundnut', 'unit': 'kg', 'min_price': 500, 'max_price': 900},
            
            # Tubers
            {'title': 'Fresh Yam Tubers', 'category': 'Tubers', 'crop': 'Yam', 'unit': 'tuber', 'min_price': 800, 'max_price': 2000},
            {'title': 'Sweet Potatoes', 'category': 'Tubers', 'crop': 'Sweet Potato', 'unit': 'kg', 'min_price': 200, 'max_price': 450},
            {'title': 'Cassava Tubers', 'category': 'Tubers', 'crop': 'Cassava', 'unit': 'kg', 'min_price': 150, 'max_price': 350},
        ]
        
        descriptions = [
            "Fresh, high-quality produce directly from our farm. Carefully harvested and sorted for premium quality.",
            "Organically grown using sustainable farming practices. No harmful chemicals or pesticides used.",
            "Farm-fresh produce available for immediate delivery. Perfect for wholesale and retail customers.",
            "Premium grade products with excellent taste and nutritional value. Ideal for families and businesses.",
            "Locally grown with traditional farming methods. Supporting local agriculture and communities.",
            "Harvest-ready produce with extended shelf life. Properly stored and handled for maximum freshness.",
            "Bulk quantities available for commercial buyers. Competitive pricing for large orders.",
            "Certified organic produce meeting international standards. Health-conscious choice for your family."
        ]
        
        locations = [
            "Abuja, FCT",
            "Lagos, Lagos State", 
            "Kano, Kano State",
            "Ibadan, Oyo State",
            "Enugu, Enugu State",
            "Kaduna, Kaduna State",
            "Jos, Plateau State",
            "Sokoto, Sokoto State",
            "Maiduguri, Borno State",
            "Calabar, Cross River State"
        ]
        
        # Get available categories, users, and crops
        categories = list(ProductCategory.objects.all())
        users = list(User.objects.all())
        crops = list(Crop.objects.filter(is_active=True))
        
        if not categories or not users or not crops:
            self.stdout.write(
                self.style.ERROR(
                    'Missing required data. Please ensure categories, users, and crops exist.'
                )
            )
            return
        
        created_count = 0
        for i in range(num_products):
            # Choose random template
            template = random.choice(product_templates)
            
            # Get or create crop
            crop, _ = Crop.objects.get_or_create(
                name=template['crop'],
                defaults={
                    'category': template['category'],
                    'growing_season': 'All year',
                    'maturity_days': random.randint(30, 120),
                    'description': f'{template["crop"]} - a nutritious and popular crop.',
                    'is_active': True
                }
            )
            
            # Get category
            try:
                category = ProductCategory.objects.get(name=template['category'])
            except ProductCategory.DoesNotExist:
                category = random.choice(categories)
            
            # Choose random user and their farm
            user = random.choice(users)
            farm = user.owned_farms.first()
            
            if not farm:
                continue
            
            # Generate product data
            price = Decimal(str(random.randint(template['min_price'], template['max_price'])))
            quantity = Decimal(str(random.randint(10, 500)))
            
            # Random organic certification
            organic_certified = random.choice([True, False, False, False])  # 25% chance
            
            # Random delivery availability
            delivery_available = random.choice([True, False, False])  # 33% chance
            
            # Generate expiry date (7-90 days from now)
            days_until_expiry = random.randint(7, 90)
            listing_expiry = timezone.now() + timedelta(days=days_until_expiry)
            
            # Create product
            product = Product.objects.create(
                title=template['title'],
                description=random.choice(descriptions),
                category=category,
                crop=crop,
                seller=user,
                farm=farm,
                quantity_available=quantity,
                unit=template['unit'],
                price_per_unit=price,
                minimum_order=Decimal(str(random.randint(1, 10))),
                quality_grade=random.choice(['grade_a', 'grade_b', 'grade_c']),
                organic_certified=organic_certified,
                pickup_location=random.choice(locations),
                delivery_available=delivery_available,
                status='active',
                listing_expiry=listing_expiry,
                featured=random.choice([True, False, False, False, False]),  # 20% chance
                view_count=random.randint(0, 100),
                inquiry_count=random.randint(0, 15)
            )
            
            # Add delivery details if delivery is available
            if delivery_available:
                product.delivery_radius_km = random.randint(5, 50)
                product.delivery_cost_per_km = Decimal(str(random.randint(10, 50)))
                product.save()
            
            # Add organic certification details if organic
            if organic_certified:
                product.certification_details = "Certified organic by Nigerian Organic Agriculture Network (NOAN). Certificate valid until next year."
                product.save()
            
            created_count += 1
            
            if created_count % 5 == 0:
                self.stdout.write(f'Created {created_count} products...')
        
        self.stdout.write(f'Successfully created {created_count} sample products!')
        
        # Print summary
        total_products = Product.objects.count()
        active_products = Product.objects.filter(status='active').count()
        featured_products = Product.objects.filter(featured=True).count()
        organic_products = Product.objects.filter(organic_certified=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'''
Sample Data Summary:
- Total Products: {total_products}
- Active Products: {active_products}
- Featured Products: {featured_products}
- Organic Products: {organic_products}
- Categories: {ProductCategory.objects.count()}
- Users: {User.objects.count()}
                '''
            )
        )