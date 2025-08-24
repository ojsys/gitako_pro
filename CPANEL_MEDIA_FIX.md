# cPanel Media Files Fix Guide

## Problem
Team member images are not showing up on the cPanel server because Django is not configured to serve media files in production.

## Root Cause
- In production (`DEBUG = False`), Django doesn't serve media files by default
- cPanel shared hosting requires special configuration to serve uploaded media files
- Media files are stored in `/public_html/media/` but not being served properly

## Solutions Implemented

### 1. Updated URL Configuration ✅
Modified `gitako/urls.py` to serve media files in production:

```python
# Serve media files in production for cPanel hosting
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 2. Enhanced cPanel Settings ✅
Updated `gitako/settings/cpanel.py` to:
- Ensure media directory exists automatically
- Set correct media paths for cPanel structure

### 3. Created Management Command ✅
Added `python manage.py fix_media_files` command to:
- Copy media files to correct locations
- Verify file paths and permissions
- Provide dry-run option for testing

## Deployment Steps

### Step 1: Update Code on Server
Upload the updated files to your cPanel server:
- `gitako/urls.py`
- `gitako/settings/cpanel.py` 
- `apps/cms/management/commands/fix_media_files.py`

### Step 2: Run Media Fix Command
```bash
# Navigate to your project directory
cd /home/yourusername/gitako_project

# Activate virtual environment
source venv/bin/activate

# Test first (dry run)
python manage.py fix_media_files --dry-run --settings=gitako.settings.cpanel

# Actually copy files
python manage.py fix_media_files --settings=gitako.settings.cpanel
```

### Step 3: Verify File Permissions
Ensure media files have correct permissions:
```bash
chmod -R 755 public_html/media/
```

### Step 4: Check Directory Structure
Your cPanel directory should look like:
```
/home/yourusername/
├── gitako_project/
│   ├── apps/
│   ├── gitako/
│   └── public_html/
│       ├── static/ (static files)
│       └── media/ (uploaded files)
│           └── cms/
│               └── team/
│                   ├── EKELE-JAMES-ADOLE.jpg
│                   ├── onahjonah.jpeg
│                   └── ANDREW.jpg
```

### Step 5: Restart Application
In cPanel Python App settings:
1. Go to "Setup Python App"
2. Find your Django application
3. Click "Restart" button

## Alternative Solution: Direct File Upload

If the above doesn't work, manually upload team images:

### Option A: Through cPanel File Manager
1. Go to cPanel File Manager
2. Navigate to `public_html/media/cms/team/`
3. Upload team member images directly

### Option B: Through FTP/SFTP
```bash
# Using SCP/SFTP
scp local_media_files/* username@server:/home/username/gitako_project/public_html/media/cms/team/
```

### Option C: Update Image References
If files are in a different location, update the database:

```python
# Django shell
python manage.py shell --settings=gitako.settings.cpanel

# Update image paths
from apps.cms.models import TeamMember
for member in TeamMember.objects.all():
    if member.image:
        print(f"{member.name}: {member.image.name}")
        # Update path if needed
        # member.image = 'cms/team/newpath.jpg'
        # member.save()
```

## Testing

### 1. Check if Images Load
Visit your website: `https://yourdomain.com/about/`
- Look for team member images
- Check browser developer tools for 404 errors

### 2. Test Direct Media URL
Try accessing media files directly:
- `https://yourdomain.com/media/cms/team/EKELE-JAMES-ADOLE.jpg`

### 3. Debug Media Serving
Add debug logging in cPanel settings:

```python
# In gitako/settings/cpanel.py
import logging
logger = logging.getLogger(__name__)

# Log media file access attempts
logger.info(f"Media root: {MEDIA_ROOT}")
logger.info(f"Media URL: {MEDIA_URL}")
```

## Common Issues & Fixes

### Issue 1: 404 Errors on Media Files
**Fix**: Ensure URL configuration includes media serving in production

### Issue 2: Permission Denied
**Fix**: Set correct file permissions:
```bash
chmod -R 755 public_html/media/
```

### Issue 3: Wrong File Paths
**Fix**: Check `MEDIA_ROOT` setting points to `public_html/media/`

### Issue 4: Files Not Copying
**Fix**: Use the management command with verbose output:
```bash
python manage.py fix_media_files --settings=gitako.settings.cpanel -v 2
```

## Support
If issues persist:
1. Check cPanel error logs
2. Enable Django debug logging  
3. Contact your hosting provider about Python app media file serving
4. Consider using external storage (AWS S3, Cloudinary) for media files

---

**Last Updated**: 2024-08-24
**Django Version**: 5.2+
**Hosting**: cPanel Shared Hosting