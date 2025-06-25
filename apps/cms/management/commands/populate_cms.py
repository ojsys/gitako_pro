from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.cms.models import (
    SiteSettings, TeamMember, Testimonial, Feature, 
    PricingPlan, FAQ, Office, HeroSection
)


class Command(BaseCommand):
    help = 'Populate CMS with default content'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Populating CMS with default content...'))
        
        # Create Site Settings
        self.create_site_settings()
        
        # Create Team Members
        self.create_team_members()
        
        # Create Testimonials
        self.create_testimonials()
        
        # Create Features
        self.create_features()
        
        # Create Pricing Plans
        self.create_pricing_plans()
        
        # Create FAQs
        self.create_faqs()
        
        # Create Offices
        self.create_offices()
        
        # Create Hero Sections
        self.create_hero_sections()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated CMS content!'))

    def create_site_settings(self):
        settings, created = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'Gitako',
                'tagline': 'Smart Farm Management for African Farmers',
                'description': 'Transform your farming with digital tools designed specifically for African agriculture',
                'email': 'hello@gitako.com',
                'phone': '+234 (0) 901 234 5678',
                'address': 'Plot 123, Victoria Island, Lagos, Nigeria',
                'twitter_url': 'https://twitter.com/gitako',
                'facebook_url': 'https://facebook.com/gitako',
                'linkedin_url': 'https://linkedin.com/company/gitako',
                'instagram_url': 'https://instagram.com/gitako',
                'active_farmers': 1000,
                'hectares_managed': 5000,
                'yield_increase_percentage': 25,
                'revenue_generated': '₦2.5B'
            }
        )
        if created:
            self.stdout.write('Created site settings')

    def create_team_members(self):
        team_members = [
            {
                'name': 'Dr. Adebayo Ogundimu',
                'title': 'CEO & Co-Founder',
                'role': 'ceo',
                'bio': 'Agricultural economist with 15+ years experience in sustainable farming practices. PhD in Agricultural Economics from University of Ibadan.',
                'email': 'adebayo@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/adebayo-ogundimu',
                'sort_order': 1
            },
            {
                'name': 'Fatima Aliyu',
                'title': 'CTO & Co-Founder',
                'role': 'cto',
                'bio': 'Full-stack developer and AI specialist. Former software engineer at Google with expertise in machine learning applications for agriculture.',
                'email': 'fatima@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/fatima-aliyu',
                'sort_order': 2
            },
            {
                'name': 'Chukwu Emeka',
                'title': 'Head of Product',
                'role': 'head',
                'bio': 'Product manager with background in agtech startups. Specializes in user experience design and product strategy for agricultural technology solutions.',
                'email': 'emeka@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/chukwu-emeka',
                'sort_order': 3
            },
            {
                'name': 'Aisha Muhammad',
                'title': 'Head of Sales & Marketing',
                'role': 'head',
                'bio': 'Marketing strategist with deep understanding of African agricultural markets. Former business development manager at leading agribusiness companies.',
                'email': 'aisha@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/aisha-muhammad',
                'sort_order': 4
            },
            {
                'name': 'Ibrahim Suleiman',
                'title': 'Lead Data Scientist',
                'role': 'developer',
                'bio': 'Data scientist specializing in agricultural analytics and predictive modeling. MSc in Data Science with focus on climate-smart agriculture applications.',
                'email': 'ibrahim@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/ibrahim-suleiman',
                'sort_order': 5
            },
            {
                'name': 'Grace Okoro',
                'title': 'Head of Customer Success',
                'role': 'head',
                'bio': 'Customer success specialist with passion for farmer education and support. Background in agricultural extension services and farmer training programs.',
                'email': 'grace@gitako.com',
                'linkedin_url': 'https://linkedin.com/in/grace-okoro',
                'sort_order': 6
            }
        ]
        
        for member_data in team_members:
            member, created = TeamMember.objects.get_or_create(
                email=member_data['email'],
                defaults=member_data
            )
            if created:
                self.stdout.write(f'Created team member: {member.name}')

    def create_testimonials(self):
        testimonials = [
            {
                'customer_name': 'Musa Abdullahi',
                'customer_title': 'Rice Farmer',
                'customer_location': 'Kebbi State',
                'testimonial_text': 'Gitako has transformed how I manage my 5-hectare rice farm. The crop calendar helps me plan perfectly, and I\'ve increased my yield by 30% this season.',
                'rating': 5,
                'is_featured': True,
                'sort_order': 1
            },
            {
                'customer_name': 'Adunni Fashola',
                'customer_title': 'Vegetable Farmer',
                'customer_location': 'Ogun State',
                'testimonial_text': 'The budget tracking feature is amazing! I can now see exactly where my money goes and plan better for the next planting season.',
                'rating': 5,
                'is_featured': True,
                'sort_order': 2
            },
            {
                'customer_name': 'John Okwu',
                'customer_title': 'Cassava Farmer',
                'customer_location': 'Enugu State',
                'testimonial_text': 'Even without internet, I can still update my farm records. When I get back online, everything syncs perfectly.',
                'rating': 4,
                'is_featured': True,
                'sort_order': 3
            }
        ]
        
        for testimonial_data in testimonials:
            testimonial, created = Testimonial.objects.get_or_create(
                customer_name=testimonial_data['customer_name'],
                customer_location=testimonial_data['customer_location'],
                defaults=testimonial_data
            )
            if created:
                self.stdout.write(f'Created testimonial: {testimonial.customer_name}')

    def create_features(self):
        features = [
            {
                'name': 'Smart Crop Calendar',
                'short_description': 'AI-powered planting and harvesting schedule',
                'detailed_description': 'Get personalized farming schedules based on your location, crop type, and weather patterns.',
                'icon': 'event_available',
                'feature_type': 'core',
                'benefits': ['Optimal planting times', 'Weather-based recommendations', 'Harvest predictions'],
                'sort_order': 1
            },
            {
                'name': 'Budget Management',
                'short_description': 'Track expenses and maximize profitability',
                'detailed_description': 'Monitor farm expenses, track income, and get insights on profitability.',
                'icon': 'account_balance_wallet',
                'feature_type': 'core',
                'benefits': ['Expense tracking', 'Profit analysis', 'Budget planning'],
                'sort_order': 2
            },
            {
                'name': 'Inventory Management',
                'short_description': 'Manage supplies, equipment, and storage',
                'detailed_description': 'Keep track of seeds, fertilizers, equipment, and harvest storage.',
                'icon': 'inventory_2',
                'feature_type': 'core',
                'benefits': ['Stock monitoring', 'Reorder alerts', 'Equipment tracking'],
                'sort_order': 3
            },
            {
                'name': 'Marketplace Access',
                'short_description': 'Connect with buyers and suppliers',
                'detailed_description': 'Buy inputs at wholesale prices and sell produce directly to buyers.',
                'icon': 'store',
                'feature_type': 'advanced',
                'benefits': ['Direct market access', 'Better prices', 'Reduced middlemen'],
                'sort_order': 4
            }
        ]
        
        for feature_data in features:
            feature, created = Feature.objects.get_or_create(
                name=feature_data['name'],
                defaults=feature_data
            )
            if created:
                self.stdout.write(f'Created feature: {feature.name}')

    def create_pricing_plans(self):
        plans = [
            {
                'name': 'Starter',
                'price': 2500.00,
                'currency': '₦',
                'billing_period': 'month',
                'description': 'Perfect for small-scale farmers and those getting started with digital farming',
                'features': [
                    'Up to 2 hectares',
                    'Basic crop calendar',
                    'Budget tracking',
                    'Basic inventory management',
                    'Mobile app access',
                    'Email support'
                ],
                'button_text': 'Start Free Trial',
                'button_url': '/auth/register/',
                'sort_order': 1
            },
            {
                'name': 'Professional',
                'price': 7500.00,
                'currency': '₦',
                'billing_period': 'month',
                'description': 'Ideal for medium-scale farmers who want advanced features and analytics',
                'features': [
                    'Up to 10 hectares',
                    'Advanced crop calendar',
                    'Complete budget management',
                    'Full inventory & equipment tracking',
                    'Block management',
                    'AI recommendations',
                    'Marketplace access',
                    'Priority support'
                ],
                'is_featured': True,
                'button_text': 'Start Free Trial',
                'button_url': '/auth/register/',
                'sort_order': 2
            },
            {
                'name': 'Enterprise',
                'price': 0.00,  # Custom pricing
                'currency': '₦',
                'billing_period': 'custom',
                'description': 'For large farms, cooperatives, and agricultural organizations',
                'features': [
                    'Unlimited hectares',
                    'All features included',
                    'Multi-farm management',
                    'Staff management',
                    'Advanced analytics',
                    'API access',
                    'Custom integrations',
                    'Dedicated support'
                ],
                'button_text': 'Contact Sales',
                'button_url': '/cms/contact/',
                'sort_order': 3
            }
        ]
        
        for plan_data in plans:
            plan, created = PricingPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created pricing plan: {plan.name}')

    def create_faqs(self):
        faqs = [
            {
                'question': 'Is there really a free trial?',
                'answer': 'Yes! We offer a full 30-day free trial with no credit card required. You\'ll have access to all features of your chosen plan during the trial period.',
                'category': 'Pricing',
                'sort_order': 1
            },
            {
                'question': 'Can I upgrade or downgrade my plan?',
                'answer': 'Absolutely! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and billing is prorated.',
                'category': 'Pricing',
                'sort_order': 2
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept all major credit cards, bank transfers, and mobile money payments. All transactions are secure and encrypted.',
                'category': 'Pricing',
                'sort_order': 3
            },
            {
                'question': 'Does Gitako work offline?',
                'answer': 'Yes! Gitako is designed as a Progressive Web App that works offline. You can update your farm data without internet, and it will sync when you\'re back online.',
                'category': 'Technical',
                'sort_order': 4
            },
            {
                'question': 'Is my data secure?',
                'answer': 'Absolutely. We use industry-standard encryption and security measures to protect your data. Your farm information is private and secure.',
                'category': 'Technical',
                'sort_order': 5
            }
        ]
        
        for faq_data in faqs:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(f'Created FAQ: {faq.question[:50]}...')

    def create_offices(self):
        offices = [
            {
                'name': 'Lagos Office',
                'address': 'Plot 123, Victoria Island, Lagos, Nigeria',
                'phone': '+234 (0) 901 234 5678',
                'email': 'lagos@gitako.com',
                'business_hours': 'Mon - Fri: 8:00 AM - 6:00 PM',
                'is_headquarters': True,
                'sort_order': 1
            },
            {
                'name': 'Abuja Office',
                'address': 'Suite 45, Central Business District, Abuja, Nigeria',
                'phone': '+234 (0) 902 345 6789',
                'email': 'abuja@gitako.com',
                'business_hours': 'Mon - Fri: 8:00 AM - 5:00 PM',
                'sort_order': 2
            },
            {
                'name': 'Kano Office',
                'address': 'No. 67, Farm Center Road, Kano, Nigeria',
                'phone': '+234 (0) 903 456 7890',
                'email': 'kano@gitako.com',
                'business_hours': 'Mon - Fri: 8:00 AM - 5:00 PM',
                'sort_order': 3
            }
        ]
        
        for office_data in offices:
            office, created = Office.objects.get_or_create(
                name=office_data['name'],
                defaults=office_data
            )
            if created:
                self.stdout.write(f'Created office: {office.name}')

    def create_hero_sections(self):
        hero_sections = [
            {
                'page': 'home',
                'title': 'Transform Your Farm with Smart Digital Tools',
                'subtitle': 'Join thousands of African farmers using Gitako to increase yields, reduce costs, and grow profitable agricultural businesses.',
                'primary_button_text': 'Start Free Trial',
                'primary_button_url': '/auth/register/',
                'secondary_button_text': 'Watch Demo',
                'secondary_button_url': '/cms/features/'
            },
            {
                'page': 'about',
                'title': 'Empowering African Farmers with Digital Innovation',
                'subtitle': 'Born from a deep understanding of African agriculture, Gitako combines cutting-edge technology with local farming expertise to revolutionize how farmers manage their operations.',
            },
            {
                'page': 'features',
                'title': 'Everything You Need to Manage Your Farm',
                'subtitle': 'From crop planning to harvest tracking, Gitako provides comprehensive tools designed specifically for African farming conditions.',
                'primary_button_text': 'Start Free Trial',
                'primary_button_url': '/auth/register/',
                'secondary_button_text': 'View Pricing',
                'secondary_button_url': '/cms/pricing/'
            },
            {
                'page': 'pricing',
                'title': 'Simple Pricing for Every Farm',
                'subtitle': 'Choose the plan that fits your farm size and needs. All plans include our core features with no hidden fees or surprise charges.',
            },
            {
                'page': 'contact',
                'title': 'Get in Touch with Our Team',
                'subtitle': 'Whether you need support, want to learn more about our features, or discuss partnership opportunities, we\'re here to help you succeed.',
            },
            {
                'page': 'offline',
                'title': 'You\'re Currently Offline',
                'subtitle': 'Don\'t worry! Gitako is designed to work offline. You can continue managing your farm, and everything will sync automatically when you\'re back online.',
            }
        ]
        
        for hero_data in hero_sections:
            hero, created = HeroSection.objects.get_or_create(
                page=hero_data['page'],
                defaults=hero_data
            )
            if created:
                self.stdout.write(f'Created hero section: {hero.page}')