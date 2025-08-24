import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.cms.models import TeamMember


class Command(BaseCommand):
    help = 'Diagnose media file serving issues on cPanel'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== MEDIA FILES DIAGNOSIS ==='))
        
        # 1. Check Django settings
        self.stdout.write('\n1. DJANGO SETTINGS:')
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        self.stdout.write(f'   MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'   MEDIA_ROOT: {settings.MEDIA_ROOT}')
        
        # 2. Check if MEDIA_ROOT directory exists
        self.stdout.write('\n2. MEDIA_ROOT DIRECTORY:')
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            self.stdout.write(f'   ✓ EXISTS: {media_root}')
            self.stdout.write(f'   ✓ IS_DIR: {media_root.is_dir()}')
            
            # Check permissions
            try:
                test_file = media_root / 'test_write.txt'
                test_file.write_text('test')
                test_file.unlink()
                self.stdout.write('   ✓ WRITABLE: Yes')
            except:
                self.stdout.write('   ✗ WRITABLE: No')
        else:
            self.stdout.write(f'   ✗ NOT FOUND: {media_root}')
            self.stdout.write('   → Creating directory...')
            try:
                media_root.mkdir(parents=True, exist_ok=True)
                self.stdout.write('   ✓ CREATED')
            except Exception as e:
                self.stdout.write(f'   ✗ CREATE FAILED: {e}')
        
        # 3. Check team images directory
        self.stdout.write('\n3. TEAM IMAGES DIRECTORY:')
        team_dir = media_root / 'cms' / 'team'
        if team_dir.exists():
            self.stdout.write(f'   ✓ EXISTS: {team_dir}')
            
            # List files
            files = list(team_dir.glob('*'))
            self.stdout.write(f'   FILES COUNT: {len(files)}')
            for file_path in files:
                if file_path.is_file():
                    size = file_path.stat().st_size
                    self.stdout.write(f'     - {file_path.name} ({size} bytes)')
        else:
            self.stdout.write(f'   ✗ NOT FOUND: {team_dir}')
            self.stdout.write('   → Creating directory...')
            try:
                team_dir.mkdir(parents=True, exist_ok=True)
                self.stdout.write('   ✓ CREATED')
            except Exception as e:
                self.stdout.write(f'   ✗ CREATE FAILED: {e}')
        
        # 4. Check team member records
        self.stdout.write('\n4. TEAM MEMBER RECORDS:')
        team_members = TeamMember.objects.filter(is_active=True)
        self.stdout.write(f'   ACTIVE MEMBERS: {team_members.count()}')
        
        for member in team_members:
            self.stdout.write(f'\n   MEMBER: {member.name}')
            if member.image:
                self.stdout.write(f'     Image field: {member.image.name}')
                self.stdout.write(f'     Image URL: {member.image.url}')
                
                # Check if physical file exists
                try:
                    file_path = Path(member.image.path)
                    if file_path.exists():
                        size = file_path.stat().st_size
                        self.stdout.write(f'     ✓ FILE EXISTS: {file_path} ({size} bytes)')
                    else:
                        self.stdout.write(f'     ✗ FILE MISSING: {file_path}')
                except Exception as e:
                    self.stdout.write(f'     ✗ PATH ERROR: {e}')
            else:
                self.stdout.write('     ✗ NO IMAGE')
        
        # 5. Test URL pattern
        self.stdout.write('\n5. URL PATTERNS TEST:')
        from django.urls import reverse, NoReverseMatch
        try:
            # Test if our custom media serving URL works
            test_url = f"{settings.MEDIA_URL}cms/team/EKELE-JAMES-ADOLE.jpg"
            self.stdout.write(f'   Expected URL: {test_url}')
        except Exception as e:
            self.stdout.write(f'   ✗ URL ERROR: {e}')
        
        # 6. Environment information
        self.stdout.write('\n6. ENVIRONMENT:')
        self.stdout.write(f'   Python path: {os.getcwd()}')
        self.stdout.write(f'   BASE_DIR: {settings.BASE_DIR}')
        
        # Check if running on cPanel
        if 'public_html' in str(settings.MEDIA_ROOT):
            self.stdout.write('   ✓ DETECTED: cPanel environment')
        else:
            self.stdout.write('   ⚠ WARNING: Not cPanel environment')
        
        self.stdout.write(f'\n{self.style.SUCCESS("=== DIAGNOSIS COMPLETE ===")}')
        
        # Provide recommendations
        self.stdout.write('\n📋 RECOMMENDATIONS:')
        self.stdout.write('1. Upload this diagnosis to your cPanel server')
        self.stdout.write('2. Run: python manage.py diagnose_media --settings=gitako.settings.cpanel')
        self.stdout.write('3. Check if files exist in the expected locations')
        self.stdout.write('4. Verify file permissions (chmod 755)')
        self.stdout.write('5. Restart your Python app in cPanel')
        self.stdout.write('6. Test the media URLs directly in browser')