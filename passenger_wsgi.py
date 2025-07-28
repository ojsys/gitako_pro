#!/usr/bin/env python3
"""
WSGI configuration for cPanel hosting with Passenger
This file is used by cPanel's Python app hosting
"""

import os
import sys

# Add your project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gitako.settings.cpanel')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()