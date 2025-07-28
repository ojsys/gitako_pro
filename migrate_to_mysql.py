#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to MySQL
Run this script after setting up MySQL database and before deploying to cPanel
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/path/to/your/project')  # Update this path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gitako.settings.cpanel')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connections
from django.core.management.base import BaseCommand

def migrate_to_mysql():
    """
    Step-by-step migration process
    """
    print("Starting migration from SQLite to MySQL...")
    
    # Step 1: Create MySQL database tables
    print("\n1. Creating MySQL database tables...")
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    # Step 2: Load initial data if needed
    print("\n2. Loading initial data...")
    try:
        execute_from_command_line(['manage.py', 'loaddata', 'initial_data.json'])
    except:
        print("No initial data fixture found, skipping...")
    
    # Step 3: Create superuser (optional)
    print("\n3. Creating superuser account...")
    print("You can create a superuser account manually using:")
    print("python manage.py createsuperuser")
    
    print("\nMigration completed successfully!")
    print("Next steps:")
    print("1. Update your .env file with MySQL database credentials")
    print("2. Test the application locally with MySQL")
    print("3. Upload files to cPanel hosting")

if __name__ == '__main__':
    migrate_to_mysql()