# Django Application Deployment Guide for cPanel Hosting

This guide will help you deploy your Django Gitako farm management application to a cPanel hosting provider with MySQL database.

## Prerequisites

- cPanel hosting account with Python support
- MySQL database access
- SSH access (recommended)
- Domain name configured

## Step 1: Prepare Your Local Environment

### 1.1 Install MySQL Client
```bash
pip install mysqlclient
```

### 1.2 Set Up Environment Variables
1. Copy `.env.example` to `.env`
2. Update the following values:
   ```env
   SECRET_KEY=your-generated-secret-key
   DEBUG=False
   DJANGO_SETTINGS_MODULE=gitako.settings.cpanel
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   
   DB_NAME=your_cpanel_database_name
   DB_USER=your_cpanel_database_user
   DB_PASSWORD=your_cpanel_database_password
   DB_HOST=localhost
   DB_PORT=3306
   
   EMAIL_HOST=mail.yourdomain.com
   EMAIL_HOST_USER=noreply@yourdomain.com
   EMAIL_HOST_PASSWORD=your_email_password
   ```

### 1.3 Generate Secret Key
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## Step 2: Set Up MySQL Database on cPanel

### 2.1 Create Database
1. Log into cPanel
2. Go to "MySQL Databases"
3. Create a new database (e.g., `username_gitako`)
4. Create a database user
5. Add user to database with ALL PRIVILEGES

### 2.2 Note Database Credentials
- Database name: `cpanel_username_dbname`
- Database user: `cpanel_username_dbuser`
- Database password: `your_chosen_password`
- Host: `localhost`

## Step 3: Prepare Application Files

### 3.1 Install Dependencies Locally
```bash
pip install -r requirements.txt
```

### 3.2 Test MySQL Connection
```bash
export DJANGO_SETTINGS_MODULE=gitako.settings.cpanel
python manage.py check --deploy
```

### 3.3 Create and Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3.4 Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 3.5 Create Superuser
```bash
python manage.py createsuperuser
```

## Step 4: Upload Files to cPanel

### 4.1 Create Directory Structure
In your cPanel File Manager or via SSH, create:
```
public_html/
├── static/          # Static files
├── media/           # Media files
├── logs/            # Log files
└── cache/           # Cache files
```

### 4.2 Upload Application Files
Upload all files except:
- `venv/` (virtual environment)
- `db.sqlite3` (SQLite database)
- `__pycache__/` directories
- `.git/` directory

### 4.3 Key Files to Upload
- All Python application files
- `requirements.txt`
- `passenger_wsgi.py`
- `.htaccess`
- `.env` (with production values)
- `staticfiles/` directory contents to `public_html/static/`

## Step 5: Configure Python App in cPanel

### 5.1 Set Up Python App
1. Go to "Python App" in cPanel
2. Create New App:
   - Python version: 3.8+ (latest available)
   - Application root: `/public_html`
   - Application URL: your domain
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`

### 5.2 Install Dependencies
In the Python App interface:
1. Click "Open Terminal"
2. Run: `pip install -r requirements.txt`

### 5.3 Set Environment Variables
In Python App configuration, add:
- `DJANGO_SETTINGS_MODULE`: `gitako.settings.cpanel`

## Step 6: Database Migration

### 6.1 Run Migrations
```bash
cd /home/username/public_html
python manage.py migrate
```

### 6.2 Create Superuser
```bash
python manage.py createsuperuser
```

### 6.3 Load Initial Data (if applicable)
```bash
python manage.py loaddata initial_data.json
```

## Step 7: Configure Static Files

### 7.1 Update Static Files Path
Ensure static files are accessible at `/static/` URL

### 7.2 Set Proper Permissions
```bash
chmod 755 public_html/static/
chmod 755 public_html/media/
```

## Step 8: Final Configuration

### 8.1 Test Application
1. Visit your domain
2. Check admin panel: `yourdomain.com/admin/`
3. Test user registration and login

### 8.2 Configure Email
Update email settings in your `.env` file with your hosting provider's SMTP details.

### 8.3 Set Up SSL Certificate
Enable SSL in cPanel for secure connections.

## Step 9: Ongoing Maintenance

### 9.1 Updating the Application
1. Upload new files
2. Run migrations if needed: `python manage.py migrate`
3. Collect static files: `python manage.py collectstatic`
4. Restart Python app in cPanel

### 9.2 Monitoring
- Check logs in `/home/username/logs/`
- Monitor database performance
- Regular backups of database and media files

## Troubleshooting

### Common Issues

1. **Internal Server Error**
   - Check error logs in cPanel
   - Verify `.env` file settings
   - Ensure all dependencies are installed

2. **Static Files Not Loading**
   - Check static files path in settings
   - Verify file permissions
   - Run `collectstatic` command

3. **Database Connection Issues**
   - Verify database credentials
   - Check database user permissions
   - Test connection in Django shell

4. **Email Not Working**
   - Verify SMTP settings
   - Check hosting provider's email configuration
   - Test with a simple email send

### Support Commands

```bash
# Check Django configuration
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# View logs
tail -f logs/django.log

# Restart Python app
# Use cPanel Python App interface to restart
```

## Security Checklist

- [ ] DEBUG is set to False
- [ ] SECRET_KEY is unique and secure
- [ ] ALLOWED_HOSTS is properly configured
- [ ] SSL certificate is installed
- [ ] Database credentials are secure
- [ ] File permissions are set correctly
- [ ] Sensitive files are protected by .htaccess

## Performance Optimization

1. Enable caching in Django settings
2. Optimize database queries
3. Use CDN for static files (optional)
4. Enable Gzip compression
5. Monitor application performance

Your Django application should now be successfully deployed on cPanel hosting with MySQL database!