from django.core.management.base import BaseCommand
from django.conf import settings
from apps.cms.models import TeamMember
import os
import shutil


class Command(BaseCommand):
    help = 'Copy media files to the correct location for cPanel hosting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be copied without actually copying files',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be copied'))
        
        # Get current media root from settings
        media_root = settings.MEDIA_ROOT
        
        self.stdout.write(f'Media root: {media_root}')
        
        # Ensure the media directories exist
        team_dir = os.path.join(media_root, 'cms', 'team')
        if not dry_run:
            os.makedirs(team_dir, exist_ok=True)
            self.stdout.write(f'Created directory: {team_dir}')
        else:
            self.stdout.write(f'Would create directory: {team_dir}')
        
        # Check team member images
        team_members = TeamMember.objects.filter(is_active=True)
        for member in team_members:
            if member.image and member.image.name:
                source_path = member.image.path
                target_path = os.path.join(media_root, member.image.name)
                
                if os.path.exists(source_path):
                    if not dry_run:
                        # Ensure target directory exists
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        # Copy the file
                        shutil.copy2(source_path, target_path)
                        self.stdout.write(
                            self.style.SUCCESS(f'Copied: {member.name} -> {target_path}')
                        )
                    else:
                        self.stdout.write(f'Would copy: {source_path} -> {target_path}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Source file not found: {source_path} for {member.name}')
                    )
            else:
                self.stdout.write(f'No image for: {member.name}')
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Media files copying completed!'))
        else:
            self.stdout.write(self.style.SUCCESS('DRY RUN completed. Use without --dry-run to actually copy files.'))