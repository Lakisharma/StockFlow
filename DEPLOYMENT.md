# StockFlow AI — Production Deployment & Hosting Guide

This guide provides step-by-step instructions for deploying the **StockFlow AI** Enterprise Warehouse & Inventory Management System to production environments (AWS, DigitalOcean, Heroku, Render, Linode, Docker, or Private On-Premise Servers).

---

## 🏗️ 1. Architecture Overview

```
                          [ SSL / HTTPS ]
                                 │
                   ┌─────────────┴─────────────┐
                   │    Nginx Reverse Proxy     │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │   Gunicorn WSGI Server    │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │    Django Backend API     │
                   └──────┬─────────────┬──────┘
                          │             │
        ┌─────────────────┴─┐         ┌─┴────────────────┐
        │ PostgreSQL DB     │         │ WhiteNoise / S3 │
        │ (Persistent Data) │         │ (Static Assets)  │
        └───────────────────┘         └──────────────────┘
```

---

## ⚙️ 2. Prerequisites & System Requirements

- **Operating System**: Ubuntu 22.04 LTS / Debian 12 / RHEL 9 / Windows Server 2022
- **Python**: Version 3.10, 3.11, or 3.12
- **Database**: PostgreSQL 14+ (or MySQL 8+)
- **Reverse Proxy**: Nginx 1.18+ with SSL (Let's Encrypt / Certbot)
- **WSGI Server**: Gunicorn 21.2+

---

## 🔑 3. Environment Variables Configuration

Create a `.env` file in the project root directory (`/var/www/stockflow/`):

```bash
# Django Production Settings
SECRET_KEY=e83a9d7f42b10c658e3f912a7d8c4e0b5f1a6c8e3d2b9f0a7c4e1d5b8f2a9c0
DEBUG=False
ALLOWED_HOSTS=stockflow.example.com,www.example.com,YOUR_SERVER_IP
CSRF_TRUSTED_ORIGINS=https://stockflow.example.com,https://www.example.com
CORS_ALLOWED_ORIGINS=https://stockflow.example.com,https://www.example.com

# PostgreSQL Database Connection
DATABASE_URL=postgres://stockflow_db_user:StrongPassword123!@localhost:5432/stockflow_db

# File Upload Limits
MAX_UPLOAD_SIZE_MB=10

# Security Redirect (Enable when SSL/HTTPS is active)
SECURE_SSL_REDIRECT=True

# Optional Email SMTP Settings
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your_actual_api_key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=StockFlow AI <notifications@example.com>
```

---

## 📦 4. Deployment Execution Steps

### Step 1: Clone Repository & Setup Virtual Environment
```bash
cd /var/www
git clone https://github.com/your-org/stockflow-ai.git stockflow
cd stockflow

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Database Setup & Migrations
```bash
# Verify database connection and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create Production Superuser
python manage.py createsuperuser
```

### Step 3: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

---

## 🚀 5. Gunicorn WSGI Server Configuration

Create a Systemd service unit `/etc/systemd/system/stockflow.service`:

```ini
[Unit]
Description=StockFlow AI Gunicorn Daemon
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/stockflow
EnvironmentFile=/var/www/stockflow/.env
ExecStart=/var/www/stockflow/venv/bin/gunicorn \
          --access-logfile /var/log/stockflow/access.log \
          --error-logfile /var/log/stockflow/error.log \
          --workers 4 \
          --bind unix:/var/www/stockflow/stockflow.sock \
          core.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable Gunicorn daemon:
```bash
sudo mkdir -p /var/log/stockflow
sudo chown -R www-data:www-data /var/log/stockflow
sudo systemctl daemon-reload
sudo systemctl start stockflow
sudo systemctl enable stockflow
```

---

## 🌐 6. Nginx Web Server & SSL Setup

Create Nginx site configuration `/etc/nginx/sites-available/stockflow`:

```nginx
server {
    listen 80;
    server_name stockflow.example.com www.example.com;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/stockflow/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/stockflow/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/stockflow/stockflow.sock;
    }
}
```

Enable Nginx configuration & obtain SSL Certificate:
```bash
sudo ln -s /etc/nginx/sites-available/stockflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Install Let's Encrypt Free SSL Certificate
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d stockflow.example.com -d www.example.com
```

---

## 🩺 7. Health Check Verification & Diagnostics

To verify application health, send an HTTP GET request to the `/health/` endpoint:

```bash
curl -I https://stockflow.example.com/health/
```

Expected Response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "storage": "healthy"
}
```

---

## 🛡️ 8. Backup & Maintenance Checklist

1. **Automated Daily Database Backups**:
   ```bash
   # Add to crontab (crontab -e) for daily 2 AM backup
   0 2 * * * pg_dump -U stockflow_db_user stockflow_db | gzip > /var/backups/stockflow_$(date +\%Y\%m\%d).sql.gz
   ```
2. **Log Rotation**: Logs are automatically written to `/var/log/stockflow/error.log`.
3. **Emergency Restore**: To restore from a backup:
   ```bash
   gunzip -c /var/backups/stockflow_20260811.sql.gz | psql -U stockflow_db_user stockflow_db
   ```
