from django.core.management.base import BaseCommand
from django.conf import settings
from apps.cms.models import TeamMember
import os
import shutil
from pathlib import Path


class Command(BaseCommand):
    help = 'Fix media files location for cPanel hosting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--move-to-public-html',
            action='store_true',
            help='Move files from media/ to public_html/media/',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        move_to_public_html = options['move_to_public_html']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be modified'))
        
        # Get current media root from settings
        media_root = Path(settings.MEDIA_ROOT)
        base_dir = Path(settings.BASE_DIR)
        
        # Possible locations for media files
        locations = [
            base_dir / 'media',
            base_dir / 'public_html' / 'media',
        ]
        
        self.stdout.write(f'Current MEDIA_ROOT setting: {media_root}')
        self.stdout.write(f'BASE_DIR: {base_dir}')
        
        # Find where files actually exist
        self.stdout.write('\n🔍 Scanning for existing media files...')
        for location in locations:
            team_dir = location / 'cms' / 'team'
            if team_dir.exists():
                files = list(team_dir.glob('*.*'))
                if files:
                    self.stdout.write(f'✓ Found {len(files)} files in: {team_dir}')
                    for file_path in files:
                        self.stdout.write(f'  - {file_path.name} ({file_path.stat().st_size} bytes)')
                else:
                    self.stdout.write(f'✓ Directory exists but empty: {team_dir}')
            else:
                self.stdout.write(f'✗ Not found: {team_dir}')
        
        # Check team member database records
        self.stdout.write(f'\n📊 Team member database records:')
        team_members = TeamMember.objects.filter(is_active=True)
        files_with_images = []
        files_without_images = []
        
        for member in team_members:
            if member.image and member.image.name:
                files_with_images.append(member)
                self.stdout.write(f'✓ {member.name}: {member.image.name}')
                
                # Check if file exists at the expected location
                expected_path = media_root / member.image.name
                if expected_path.exists():
                    self.stdout.write(f'  ✓ File exists at: {expected_path}')
                else:
                    self.stdout.write(f'  ✗ File missing at: {expected_path}')
                    
                    # Look for file in other locations
                    for location in locations:
                        alt_path = location / member.image.name
                        if alt_path.exists():
                            self.stdout.write(f'  ✓ Found file at: {alt_path}')
                            
                            if move_to_public_html:
                                # Move file to public_html location
                                public_html_path = base_dir / 'public_html' / 'media' / member.image.name
                                if not dry_run:
                                    os.makedirs(public_html_path.parent, exist_ok=True)
                                    shutil.move(str(alt_path), str(public_html_path))
                                    self.stdout.write(f'  ✓ Moved: {alt_path} → {public_html_path}')
                                else:
                                    self.stdout.write(f'  → Would move: {alt_path} → {public_html_path}')
                            break
            else:
                files_without_images.append(member)
                self.stdout.write(f'✗ {member.name}: No image')
        
        # Summary
        self.stdout.write(f'\n📋 Summary:')
        self.stdout.write(f'  Team members with images: {len(files_with_images)}')
        self.stdout.write(f'  Team members without images: {len(files_without_images)}')
        
        # Recommendations
        self.stdout.write(f'\n💡 Recommendations:')
        
        # Check if files are in public_html but MEDIA_ROOT points elsewhere
        public_html_media = base_dir / 'public_html' / 'media' / 'cms' / 'team'
        regular_media = base_dir / 'media' / 'cms' / 'team'
        
        if public_html_media.exists() and list(public_html_media.glob('*.*')):
            if str(media_root) != str(base_dir / 'public_html' / 'media'):
                self.stdout.write('  ⚠️  Files are in public_html/media/ but MEDIA_ROOT points elsewhere')
                self.stdout.write('  📝 Update MEDIA_ROOT in settings/cpanel.py to:')
                self.stdout.write(f'     MEDIA_ROOT = BASE_DIR / "public_html" / "media"')
            else:
                self.stdout.write('  ✓ Files are in correct location for cPanel serving')
        elif regular_media.exists() and list(regular_media.glob('*.*')):
            self.stdout.write('  ✓ Files are in media/ directory')
            self.stdout.write('  💡 For cPanel, consider moving to public_html/media/ using:')
            self.stdout.write('     python manage.py fix_media_files --move-to-public-html')
        
        if not dry_run and not move_to_public_html:
            self.stdout.write('\n✅ Analysis complete! Use --move-to-public-html if you need to move files.')