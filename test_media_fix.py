#!/usr/bin/env python3
"""
Quick test script to verify media configuration on cPanel
Run this after uploading the fixed files
"""

import os
import sys
import django
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gitako.settings.cpanel')
django.setup()

from django.conf import settings
from apps.cms.models import TeamMember

print("🔧 Media Configuration Test")
print("=" * 40)

# Check settings
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"BASE_DIR: {settings.BASE_DIR}")
print(f"DEBUG: {settings.DEBUG}")

# Check if media directory exists
media_root = Path(settings.MEDIA_ROOT)
print(f"\n📁 Media directory check:")
print(f"  Exists: {media_root.exists()}")
if media_root.exists():
    print(f"  Is directory: {media_root.is_dir()}")
    print(f"  Path: {media_root.absolute()}")

# Check team directory
team_dir = media_root / 'cms' / 'team'
print(f"\n👥 Team directory check:")
print(f"  Exists: {team_dir.exists()}")
if team_dir.exists():
    files = list(team_dir.glob('*'))
    print(f"  Files count: {len(files)}")
    for file in files:
        if file.is_file():
            size = file.stat().st_size
            print(f"    - {file.name} ({size:,} bytes)")

# Check team members in database
print(f"\n📊 Database team members:")
team_members = TeamMember.objects.filter(is_active=True)
print(f"  Active members: {team_members.count()}")

for member in team_members:
    print(f"\n  {member.name}:")
    if member.image:
        print(f"    Image field: {member.image.name}")
        print(f"    Image URL: {member.image.url}")
        
        # Check if file exists
        try:
            file_path = Path(member.image.path)
            print(f"    File path: {file_path}")
            print(f"    File exists: {file_path.exists()}")
            if file_path.exists():
                print(f"    File size: {file_path.stat().st_size:,} bytes")
        except Exception as e:
            print(f"    Error checking file: {e}")
    else:
        print("    No image")

print(f"\n✅ Test complete!")
print(f"\n📋 Next steps:")
print(f"1. Upload the updated gitako/settings/cpanel.py")
print(f"2. Restart your Python app in cPanel")
print(f"3. Test these URLs:")
print(f"   - https://gitako.com/media/cms/team/ekele.jpeg")
print(f"   - https://gitako.com/about/")
print(f"   - https://gitako.com/debug/media/")