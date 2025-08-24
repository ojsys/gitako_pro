# 🚨 URGENT: cPanel Media Files Fix

## Problem
- Media URL: `https://gitako.com/media/cms/team/EKELE-JAMES-ADOLE.jpg` returns 404
- Team member images not loading on about page
- Files exist but Django can't serve them properly

## Root Cause Analysis
Based on your error message, the issue is:
1. **MEDIA_ROOT path mismatch**: Files are in `public_html/media/` but Django settings point elsewhere
2. **Same file error**: The fix script tried to copy files to the same location they already exist
3. **URL routing**: Django can't serve files because MEDIA_ROOT doesn't match actual file location

**Your files are already in the correct location: `/home/gitakoco/gitako/public_html/media/cms/team/`**
The problem is just the Django configuration!

## 🛠️ IMMEDIATE FIXES TO DEPLOY

### Step 1: Upload Updated Files
Upload these updated files to your cPanel server:

**Files to upload:**
- `gitako/urls.py` ← **Updated URL routing**
- `gitako/settings/cpanel.py` ← **Enhanced media config**  
- `apps/cms/media_views.py` ← **NEW: Custom media serving**
- `apps/cms/management/commands/diagnose_media.py` ← **NEW: Diagnosis tool**
- `apps/cms/management/commands/fix_media_files.py` ← **File copy utility**

### Step 2: Run Diagnosis Command
```bash
# SSH into your cPanel server or use cPanel Terminal
cd ~/gitako_project

# Activate virtual environment
source venv/bin/activate

# Run diagnosis to see what's wrong
python manage.py diagnose_media --settings=gitako.settings.cpanel
```

### Step 3: Fix File Locations  
```bash
# Copy media files to correct location
python manage.py fix_media_files --settings=gitako.settings.cpanel

# Set proper permissions
chmod -R 755 public_html/media/
chmod -R 755 media/  # if files are in root media folder

# Check directory structure
ls -la public_html/media/cms/team/
```

### Step 4: Restart Python App
1. Go to cPanel → **"Setup Python App"**
2. Find your Django application  
3. Click **"Restart"** button
4. Wait for restart to complete

### Step 5: Test Media URLs
Try these URLs directly in browser:
- `https://gitako.com/media/cms/team/EKELE-JAMES-ADOLE.jpg`
- `https://gitako.com/media/cms/team/onahjonah.jpeg`
- `https://gitako.com/media/cms/team/ANDREW.jpg`

## 🔧 ALTERNATIVE SOLUTIONS

### Option A: Manual File Upload
If commands don't work, manually upload files:

1. **Via cPanel File Manager:**
   - Go to File Manager
   - Navigate to `public_html/media/cms/team/`  
   - Upload the 3 team image files directly

2. **Via FTP/SFTP:**
   ```bash
   # Upload files via SCP
   scp media/cms/team/*.jpg username@server:~/gitako_project/public_html/media/cms/team/
   ```

### Option B: Debug Media Serving
Visit debug page: `https://gitako.com/debug/media/`
- Shows media configuration
- Tests each team member image
- Displays error details

### Option C: Force Static File Serving
If Django serving doesn't work, create `.htaccess`:

Create: `public_html/media/.htaccess`
```apache
# Force media files to be served directly by Apache
<IfModule mod_rewrite.c>
    RewriteEngine Off
</IfModule>

# Set proper MIME types
<IfModule mod_mime.c>
    AddType image/jpeg .jpg .jpeg
    AddType image/png .png
    AddType image/gif .gif
</IfModule>

# Enable direct file access
Options +Indexes
```

## 📋 VERIFICATION CHECKLIST

After implementing fixes, verify:

- [ ] Files exist at: `~/gitako_project/public_html/media/cms/team/`
- [ ] File permissions are 755: `ls -la public_html/media/cms/team/`  
- [ ] Django app restarted in cPanel
- [ ] Media URLs load directly: `https://gitako.com/media/cms/team/EKELE-JAMES-ADOLE.jpg`
- [ ] About page shows team images: `https://gitako.com/about/`
- [ ] Debug page works: `https://gitako.com/debug/media/`

## 🚨 EMERGENCY FALLBACK

If nothing works, use external storage:

### Option 1: Upload to cPanel File Manager
1. Go to cPanel File Manager  
2. Navigate to `public_html/images/team/`
3. Upload team images directly
4. Update database image paths:

```python
# Django shell
python manage.py shell --settings=gitako.settings.cpanel

from apps.cms.models import TeamMember
# Update Ekele's image path
ekele = TeamMember.objects.get(name="Ekele James Adole")
ekele.image = 'images/team/EKELE-JAMES-ADOLE.jpg'  # New path
ekele.save()
```

### Option 2: Use External CDN
Quick fix - upload to external service:
- Upload images to Imgur/Cloudinary
- Update database with external URLs
- Change template to use external URLs

## 🔍 DEBUGGING INFORMATION

**Expected file structure on cPanel:**
```
/home/username/gitako_project/
├── public_html/
│   ├── media/
│   │   └── cms/
│   │       └── team/
│   │           ├── EKELE-JAMES-ADOLE.jpg
│   │           ├── onahjonah.jpeg
│   │           └── ANDREW.jpg
│   └── static/ (handled by WhiteNoise)
└── gitako/ (Django project files)
```

**Common issues:**
1. Files in wrong location (~/media/ instead of ~/public_html/media/)
2. Wrong file permissions (need 755)
3. Case sensitivity (EKELE-JAMES-ADOLE.jpg vs ekele-james-adole.jpg)
4. URL routing not working in Passenger WSGI

---

**PRIORITY: HIGH** 🔴  
**TIME TO FIX: 15-30 minutes**  
**DIFFICULTY: Medium**

Run the diagnosis command first to identify the exact issue, then apply the appropriate fix!