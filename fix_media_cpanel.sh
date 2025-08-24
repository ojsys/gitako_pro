#!/bin/bash

# cPanel Media Files Fix Script
# Run this script on your cPanel server to fix media file serving

echo "🚀 Starting cPanel Media Files Fix..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Make sure you're in the Django project directory."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Warning: No virtual environment found. Continuing anyway..."
fi

# Set Django settings for cPanel
export DJANGO_SETTINGS_MODULE=gitako.settings.cpanel

echo "🔍 Step 1: Running media diagnosis..."
python manage.py diagnose_media

echo ""
echo "📁 Step 2: Creating media directories..."
mkdir -p public_html/media/cms/team
echo "   ✓ Created: public_html/media/cms/team/"

echo ""
echo "🔄 Step 3: Copying media files..."
python manage.py fix_media_files

echo ""
echo "🔒 Step 4: Setting file permissions..."
chmod -R 755 public_html/media/
echo "   ✓ Set permissions: 755 for public_html/media/"

# Check if files exist
echo ""
echo "📋 Step 5: Verifying files..."
if [ -d "public_html/media/cms/team" ]; then
    echo "   Files in public_html/media/cms/team/:"
    ls -la public_html/media/cms/team/ || echo "   No files found"
else
    echo "   ❌ Directory not found: public_html/media/cms/team"
fi

# Also check root media directory (in case files are there)
if [ -d "media/cms/team" ]; then
    echo "   Files in media/cms/team/:"
    ls -la media/cms/team/ || echo "   No files found"
    
    echo ""
    echo "🔄 Copying files from media/ to public_html/media/..."
    cp -r media/* public_html/media/ 2>/dev/null || echo "   No files to copy"
fi

echo ""
echo "🧪 Step 6: Testing media configuration..."
python -c "
from django.conf import settings
print(f'MEDIA_URL: {settings.MEDIA_URL}')
print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')
print(f'DEBUG: {settings.DEBUG}')
"

echo ""
echo "✅ Fix script completed!"
echo "=================================="
echo "📋 Next Steps:"
echo "1. Restart your Python app in cPanel:"
echo "   → Go to 'Setup Python App'"
echo "   → Find your Django app" 
echo "   → Click 'Restart'"
echo ""
echo "2. Test these URLs in browser:"
echo "   → https://gitako.com/media/cms/team/EKELE-JAMES-ADOLE.jpg"
echo "   → https://gitako.com/about/"
echo "   → https://gitako.com/debug/media/"
echo ""
echo "3. If still not working, check the file locations:"
echo "   → ls -la ~/gitako_project/public_html/media/cms/team/"
echo ""
echo "🆘 If issues persist, check CPANEL_MEDIA_URGENT_FIX.md"