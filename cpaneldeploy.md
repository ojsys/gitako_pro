# Manual Django Deployment Steps for cPanel

## Prerequisites
- cPanel hosting account with Python support
- MySQL database access
- Domain name configured
- FTP/File Manager access

## Step 1: Prepare Local Environment

### 1.1 Generate Django Secret Key
```python
# Run this in Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
Copy the generated key for use in Step 2.

### 1.2 Test Local Setup
```bash
# Install MySQL client
pip install mysqlclient

# Test with production settings
export DJANGO_SETTINGS_MODULE=gitako.settings.cpanel
python manage.py check --deploy
```

## Step 2: Configure Environment Variables

### 2.1 Create .env File
Copy `.env.example` to `.env` and update these values:

```env
# Django Settings
SECRET_KEY=your-generated-secret-key-from-step-1
DEBUG=False
DJANGO_SETTINGS_MODULE=gitako.settings.cpanel

# Domain Configuration (replace with your actual domain)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# MySQL Database Configuration (get these from cPanel Step 3)
DB_NAME=cpanel_username_gitako
DB_USER=cpanel_username_dbuser  
DB_PASSWORD=your_chosen_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (replace with your hosting email settings)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Optional: Stripe Configuration (if using payments)
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key

# Optional: OpenAI Configuration (if using AI features)
OPENAI_API_KEY=your_openai_api_key
```

## Step 3: Set Up MySQL Database in cPanel

### 3.1 Create Database
1. Log into your cPanel account
2. Find and click "MySQL Databases"
3. Under "Create New Database":
   - Database Name: `gitako` (will become `cpanel_username_gitako`)
   - Click "Create Database"

### 3.2 Create Database User
1. Under "MySQL Users" → "Add New User":
   - Username: `dbuser` (will become `cpanel_username_dbuser`)
   - Password: Choose a strong password
   - Click "Create User"

### 3.3 Assign User to Database
1. Under "Add User To Database":
   - User: Select the user you just created
   - Database: Select the database you just created
   - Click "Add"
2. On privileges page, select "ALL PRIVILEGES"
3. Click "Make Changes"

### 3.4 Note Database Credentials
Write down these exact values for your .env file:
- DB_NAME: `cpanel_username_gitako`
- DB_USER: `cpanel_username_dbuser`
- DB_PASSWORD: `the_password_you_chose`
- DB_HOST: `localhost`
- DB_PORT: `3306`

## Step 4: Prepare Application Files

### 4.1 Collect Static Files
```bash
# Run locally
python manage.py collectstatic --noinput
```

### 4.2 Create Required Directories
Create these empty directories in your project:
- `logs/`
- `cache/`

### 4.3 Files to Upload
Prepare these files/folders for upload:
- `apps/` (entire directory)
- `gitako/` (entire directory)
- `templates/` (entire directory)
- `staticfiles/` (entire directory - will go to public_html/static/)
- `media/` (entire directory - will go to public_html/media/)
- `manage.py`
- `passenger_wsgi.py`
- `.htaccess`
- `requirements.txt`
- `.env` (with your production values)
- `logs/` (empty directory)
- `cache/` (empty directory)

### 4.4 Files NOT to Upload
Do NOT upload these:
- `venv/` or `env/` (virtual environment)
- `db.sqlite3` (SQLite database)
- `__pycache__/` directories
- `.git/` directory
- `node_modules/` (if exists)

## Step 5: Upload Files to cPanel

### 5.1 Using cPanel File Manager
1. Log into cPanel
2. Open "File Manager"
3. Navigate to your home directory (`/home/yourusername/`)
4. Upload all application files EXCEPT `staticfiles/` and `media/`
5. Extract if uploaded as zip

### 5.2 Upload Static Files
1. Navigate to `public_html/`
2. Create `static/` directory if it doesn't exist
3. Upload contents of `staticfiles/` to `public_html/static/`
4. Create `media/` directory if it doesn't exist
5. Upload contents of `media/` to `public_html/media/`

### 5.3 Set File Permissions
Set these permissions:
- Directories: 755
- Python files: 644
- `passenger_wsgi.py`: 755
- `.htaccess`: 644

## Step 6: Configure Python Application in cPanel

### 6.1 Create Python App
1. In cPanel, find and click "Python App"
2. Click "Create Application"
3. Configure:
   - **Python Version**: Select highest available (3.8, 3.9, 3.10, or 3.11)
   - **Application Root**: `/public_html`
   - **Application URL**: Leave blank (for main domain) or enter subdirectory
   - **Application Startup File**: `passenger_wsgi.py`
   - **Application Entry Point**: `application`
   - **Passenger Log File**: `/home/yourusername/logs/passenger.log`

### 6.2 Set Environment Variables
In the Python App interface:
1. Click "Environment Variables"
2. Add:
   - Name: `DJANGO_SETTINGS_MODULE`
   - Value: `gitako.settings.cpanel`

### 6.3 Install Dependencies
1. In Python App interface, click "Open Terminal" or "Terminal"
2. Run these commands:
```bash
cd $HOME
pip install -r requirements.txt
```

Wait for installation to complete (may take several minutes).

## Step 7: Database Setup

### 7.1 Run Migrations
In the Python App terminal:
```bash
cd $HOME
python manage.py migrate
```

### 7.2 Create Superuser
```bash
python manage.py createsuperuser
```
Enter username, email, and password when prompted.

### 7.3 Load Initial Data (if applicable)
```bash
# Only if you have fixture files
python manage.py loaddata initial_data.json
```

## Step 8: Configure Domain and SSL

### 8.1 Point Domain to Hosting
1. In your domain registrar, update DNS:
   - A Record: `@` → Your hosting IP address
   - CNAME Record: `www` → `yourdomain.com`

### 8.2 Install SSL Certificate
1. In cPanel, go to "SSL/TLS"
2. Click "Let's Encrypt"
3. Select your domain and install certificate

## Step 9: Test Deployment

### 9.1 Test Website
1. Visit `https://yourdomain.com`
2. Check homepage loads correctly
3. Test user registration/login
4. Test admin panel: `https://yourdomain.com/admin/`

### 9.2 Test Email
1. Try password reset functionality
2. Check contact form (if exists)
3. Verify emails are being sent

### 9.3 Check Logs
In cPanel File Manager:
1. Check `/home/yourusername/logs/django.log`
2. Check `/home/yourusername/logs/passenger.log`
3. Look for any error messages

## Step 10: Post-Deployment Tasks

### 10.1 Security Checklist
- [ ] DEBUG is set to False
- [ ] SECRET_KEY is unique and secure
- [ ] ALLOWED_HOSTS contains only your domains
- [ ] SSL certificate is active
- [ ] Database user has minimum required privileges
- [ ] Sensitive files are protected by .htaccess

### 10.2 Performance Optimization
1. Test page load speeds
2. Check static files are loading from `/static/` URL
3. Verify images are loading from `/media/` URL

### 10.3 Regular Maintenance
1. **Weekly**: Check error logs
2. **Monthly**: Update dependencies if needed
3. **Monthly**: Database backup:
```bash
mysqldump -u username_dbuser -p username_gitako > backup_$(date +%Y%m%d).sql
```

## Troubleshooting Common Issues

### Issue: Internal Server Error (500)
**Solutions:**
1. Check `/home/yourusername/logs/passenger.log`
2. Verify `.env` file has correct database credentials
3. Ensure `passenger_wsgi.py` has correct permissions (755)
4. Check Python app configuration in cPanel

### Issue: Static Files Not Loading
**Solutions:**
1. Verify files are in `public_html/static/`
2. Check `.htaccess` file is in place
3. Run `python manage.py collectstatic --noinput`
4. Check file permissions on static directory

### Issue: Database Connection Error
**Solutions:**
1. Verify database credentials in `.env`
2. Check database user has access to database
3. Test connection: `python manage.py dbshell`
4. Ensure MySQL service is running

### Issue: Email Not Working
**Solutions:**
1. Verify SMTP settings in `.env`
2. Check hosting provider's email documentation
3. Test with hosting provider's webmail
4. Check spam folders

### Issue: Admin Panel CSS Missing
**Solutions:**
1. Run `python manage.py collectstatic --noinput`
2. Check static files URL configuration
3. Verify `.htaccess` rules for static files

## Support Commands

```bash
# Check Django configuration
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# View recent logs
tail -f logs/django.log
tail -f logs/passenger.log

# Restart application (in cPanel Python App interface)
# Use "Restart" button in Python App dashboard

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Check installed packages
pip list

# Update single package
pip install --upgrade package_name
```

## Emergency Procedures

### Rollback Deployment
1. Restore previous version of files
2. Restore database from backup
3. Restart Python application

### Database Recovery
```bash
# Restore from backup
mysql -u username_dbuser -p username_gitako < backup_file.sql
```

### Reset Application
```bash
# Clear all cache
rm -rf cache/*

# Restart Python app via cPanel interface
# Or contact hosting support
```

---

**Your Django application should now be successfully deployed on cPanel hosting!**

For ongoing support, keep this guide handy and monitor your error logs regularly.