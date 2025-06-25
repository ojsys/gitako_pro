from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.farms.models import Farm, Crop, CropVariety, Block
from apps.budget.models import BudgetCategory
from apps.inventory.models import SupplyCategory
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for Gitako'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample crops
        crops_data = [
            {
                'name': 'Maize',
                'scientific_name': 'Zea mays',
                'category': 'Cereal',
                'growing_season': 'Wet Season',
                'maturity_days': 120,
                'description': 'Staple cereal crop widely cultivated in Nigeria'
            },
            {
                'name': 'Rice',
                'scientific_name': 'Oryza sativa',
                'category': 'Cereal',
                'growing_season': 'Wet Season',
                'maturity_days': 150,
                'description': 'Important cereal crop for food security'
            },
            {
                'name': 'Cassava',
                'scientific_name': 'Manihot esculenta',
                'category': 'Root Crop',
                'growing_season': 'All Year',
                'maturity_days': 365,
                'description': 'Important root crop and source of carbohydrates'
            },
            {
                'name': 'Tomato',
                'scientific_name': 'Solanum lycopersicum',
                'category': 'Vegetable',
                'growing_season': 'Dry Season',
                'maturity_days': 90,
                'description': 'Popular vegetable crop for local and export markets'
            },
            {
                'name': 'Yam',
                'scientific_name': 'Dioscorea spp.',
                'category': 'Root Crop',
                'growing_season': 'Wet Season',
                'maturity_days': 300,
                'description': 'Traditional root crop with cultural significance'
            }
        ]

        for crop_data in crops_data:
            crop, created = Crop.objects.get_or_create(
                name=crop_data['name'],
                defaults=crop_data
            )
            if created:
                self.stdout.write(f'Created crop: {crop.name}')

        # Create crop varieties
        varieties_data = [
            {'crop': 'Maize', 'name': 'Oba Super 2', 'maturity_days': 120, 'yield_per_hectare': Decimal('4.5')},
            {'crop': 'Maize', 'name': 'Sammaz 15', 'maturity_days': 110, 'yield_per_hectare': Decimal('5.0')},
            {'crop': 'Rice', 'name': 'FARO 44', 'maturity_days': 150, 'yield_per_hectare': Decimal('6.0')},
            {'crop': 'Rice', 'name': 'NERICA 1', 'maturity_days': 140, 'yield_per_hectare': Decimal('5.5')},
            {'crop': 'Tomato', 'name': 'Roma VF', 'maturity_days': 90, 'yield_per_hectare': Decimal('25.0')},
            {'crop': 'Tomato', 'name': 'UC82B', 'maturity_days': 85, 'yield_per_hectare': Decimal('30.0')},
        ]

        for variety_data in varieties_data:
            crop = Crop.objects.get(name=variety_data['crop'])
            variety, created = CropVariety.objects.get_or_create(
                crop=crop,
                name=variety_data['name'],
                defaults={
                    'maturity_days': variety_data['maturity_days'],
                    'yield_per_hectare': variety_data['yield_per_hectare']
                }
            )
            if created:
                self.stdout.write(f'Created variety: {variety.name}')

        # Create budget categories
        budget_categories = [
            {'name': 'Seeds & Planting Materials', 'icon': 'eco', 'color': '#4caf50'},
            {'name': 'Fertilizers', 'icon': 'scatter_plot', 'color': '#ff9800'},
            {'name': 'Pesticides & Herbicides', 'icon': 'bug_report', 'color': '#f44336'},
            {'name': 'Labor & Wages', 'icon': 'people', 'color': '#2196f3'},
            {'name': 'Equipment & Tools', 'icon': 'build', 'color': '#9c27b0'},
            {'name': 'Fuel & Transportation', 'icon': 'local_gas_station', 'color': '#ff5722'},
            {'name': 'Irrigation & Water', 'icon': 'water_drop', 'color': '#00bcd4'},
            {'name': 'Storage & Processing', 'icon': 'warehouse', 'color': '#795548'},
            {'name': 'Marketing & Sales', 'icon': 'store', 'color': '#607d8b'},
            {'name': 'Insurance & Loans', 'icon': 'security', 'color': '#3f51b5'},
        ]

        for cat_data in budget_categories:
            category, created = BudgetCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created budget category: {category.name}')

        # Create supply categories
        supply_categories = [
            {'name': 'Seeds', 'icon': 'eco', 'color': '#4caf50'},
            {'name': 'Fertilizers', 'icon': 'scatter_plot', 'color': '#ff9800'},
            {'name': 'Pesticides', 'icon': 'bug_report', 'color': '#f44336'},
            {'name': 'Herbicides', 'icon': 'grass', 'color': '#8bc34a'},
            {'name': 'Tools', 'icon': 'build', 'color': '#9c27b0'},
            {'name': 'Fuel', 'icon': 'local_gas_station', 'color': '#ff5722'},
            {'name': 'Packaging Materials', 'icon': 'inventory_2', 'color': '#795548'},
        ]

        for cat_data in supply_categories:
            category, created = SupplyCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created supply category: {category.name}')

        # Get admin user
        try:
            admin_user = User.objects.get(email='admin@gitako.com')
            
            # Create a sample farm
            farm, created = Farm.objects.get_or_create(
                name='Green Valley Farm',
                owner=admin_user,
                defaults={
                    'description': 'A modern integrated farming operation specializing in cereals and vegetables',
                    'total_area': Decimal('50.0'),
                    'location': 'Kaduna State, Nigeria',
                    'soil_type': 'Clay Loam',
                    'climate_zone': 'Sudan Savanna',
                    'water_source': 'Borehole and River'
                }
            )
            if created:
                self.stdout.write(f'Created farm: {farm.name}')

                # Create sample blocks
                blocks_data = [
                    {
                        'name': 'Block A',
                        'size': Decimal('15.0'),
                        'crop': Crop.objects.get(name='Maize'),
                        'variety': CropVariety.objects.filter(crop__name='Maize').first(),
                        'plant_population': 53000,
                        'expected_yield': Decimal('67.5')
                    },
                    {
                        'name': 'Block B',
                        'size': Decimal('20.0'),
                        'crop': Crop.objects.get(name='Rice'),
                        'variety': CropVariety.objects.filter(crop__name='Rice').first(),
                        'plant_population': 400000,
                        'expected_yield': Decimal('120.0')
                    },
                    {
                        'name': 'Block C',
                        'size': Decimal('10.0'),
                        'crop': Crop.objects.get(name='Tomato'),
                        'variety': CropVariety.objects.filter(crop__name='Tomato').first(),
                        'plant_population': 20000,
                        'expected_yield': Decimal('250.0')
                    }
                ]

                for block_data in blocks_data:
                    block, created = Block.objects.get_or_create(
                        farm=farm,
                        name=block_data['name'],
                        defaults=block_data
                    )
                    if created:
                        self.stdout.write(f'Created block: {block.name}')

        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('Admin user not found. Please create admin user first.'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))