# Generated manually to fix phone field length issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='phone',
            field=models.CharField(default='+234 (0) 901 234 5678', max_length=30),
        ),
        migrations.AlterField(
            model_name='office',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='contactsubmission',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]