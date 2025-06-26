from django.db import migrations


def create_default_categories(apps, schema_editor):
    ReportCategory = apps.get_model('reports', 'ReportCategory')
    
    categories = [
        {
            'name': 'Financial Reports',
            'category_type': 'financial',
            'description': 'Financial analysis, budget tracking, and profitability reports'
        },
        {
            'name': 'Production Reports',
            'category_type': 'production',
            'description': 'Crop yield analysis, production efficiency, and performance metrics'
        },
        {
            'name': 'Operational Reports',
            'category_type': 'operational',
            'description': 'Task management, equipment utilization, and operational efficiency'
        },
        {
            'name': 'Marketplace Reports',
            'category_type': 'marketplace',
            'description': 'Sales performance, market analysis, and transaction reports'
        },
        {
            'name': 'Executive Reports',
            'category_type': 'executive',
            'description': 'High-level dashboards, KPI scorecards, and strategic insights'
        },
    ]
    
    for category_data in categories:
        ReportCategory.objects.get_or_create(
            category_type=category_data['category_type'],
            defaults={
                'name': category_data['name'],
                'description': category_data['description'],
                'is_active': True
            }
        )


def reverse_create_default_categories(apps, schema_editor):
    ReportCategory = apps.get_model('reports', 'ReportCategory')
    ReportCategory.objects.filter(category_type__in=[
        'financial', 'production', 'operational', 'marketplace', 'executive'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_default_categories,
            reverse_create_default_categories
        ),
    ]