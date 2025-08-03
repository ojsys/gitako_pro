# URGENT FIX for Phone Field Error

## Problem
The CMS phone field is too short causing this error:
```
django.db.utils.DataError: (1406, "Data too long for column 'phone' at row 1")
```

## Quick Fix Steps

### Step 1: Upload the Fixed Migration
Upload the file `apps/cms/migrations/0002_fix_phone_field_length.py` to your server.

### Step 2: Run the Migration
In your cPanel Python terminal:
```bash
cd /home/gitakoco/gitako
python manage.py migrate cms
```

### Step 3: Alternative Manual Database Fix
If the migration doesn't work, fix the database directly:

1. Login to cPanel → phpMyAdmin
2. Select your database
3. Find the `cms_sitesettings` table
4. Run this SQL command:
```sql
ALTER TABLE cms_sitesettings MODIFY COLUMN phone VARCHAR(30) NOT NULL DEFAULT '+234 (0) 901 234 5678';
ALTER TABLE cms_office MODIFY COLUMN phone VARCHAR(30) NOT NULL DEFAULT '';
ALTER TABLE cms_contactsubmission MODIFY COLUMN phone VARCHAR(30) NOT NULL DEFAULT '';
```

### Step 4: Clear Any Existing Data (if needed)
If there's corrupted data:
```bash
python manage.py shell
```
Then in the Python shell:
```python
from apps.cms.models import SiteSettings
SiteSettings.objects.all().delete()
exit()
```

### Step 5: Test the Fix
Visit your website again. The phone field error should be resolved.

## Files Updated
- `apps/cms/models.py` - Increased phone field length to 30 characters
- `apps/cms/migrations/0002_fix_phone_field_length.py` - Migration to update database

## Command Summary
```bash
# In cPanel terminal
cd /home/gitakoco/gitako
python manage.py migrate cms
# Then test your website
```