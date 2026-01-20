# Deployment Guide for Image Creator on Droplet

## Current Server Setup
- **tracking-server**: Port 5001 → `tools.lemauricienltd.com`
- **subscription-server**: Port 8082 → `newsletter.lemauricienltd.com`
- **Image Creator**: Will use Port 8000 → `tools.lemauricienltd.com/image_creator`

## Deployment Steps

### 1. SSH into the droplet
```bash
ssh root@178.128.18.58
```

### 2. Create application user (if not exists)
```bash
adduser --disabled-password --gecos "" imagecreator
usermod -aG www-data imagecreator
```

### 3. Switch to application user
```bash
su - imagecreator
```

### 4. Clone the repository
```bash
cd /home/imagecreator
git clone git@github.com:8URT/Image_Creator.git
cd Image_Creator
```

### 5. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Install dependencies
```bash
pip install -r requirements.txt
```

### 7. Set up environment variables
```bash
cp env.example .env
nano .env
```

Update these values in `.env`:
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret
- `BASE_URL` - `https://tools.lemauricienltd.com` (or your domain)
- `ADMIN_EMAIL` - Your admin email
- `FLASK_ENV=production`

### 8. Initialize database
```bash
source venv/bin/activate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 9. Create systemd service
```bash
sudo nano /etc/systemd/system/image-creator.service
```

Paste this content:
```ini
[Unit]
Description=Image Creator Gunicorn daemon
After=network.target

[Service]
User=imagecreator
Group=www-data
WorkingDirectory=/home/imagecreator/Image_Creator
Environment="PATH=/home/imagecreator/Image_Creator/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/home/imagecreator/Image_Creator/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 10. Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable image-creator
sudo systemctl start image-creator
sudo systemctl status image-creator
```

### 11. Configure Nginx

**Option A: Add location block to existing tracking-server config (Recommended)**

Edit the tracking-server config:
```bash
sudo nano /etc/nginx/sites-available/tracking-server
```

Add these location blocks **BEFORE** the existing `location /` block (order matters!):
```nginx
    # Image Creator main route
    location /image_creator {
        proxy_pass http://127.0.0.1:8000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Increase body size for image uploads
        client_max_body_size 10M;
    }

    # Authentication routes (for Google OAuth and login)
    location /auth {
        proxy_pass http://127.0.0.1:8000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Admin panel routes
    location /admin {
        proxy_pass http://127.0.0.1:8000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files for Image Creator
    location /static {
        alias /home/imagecreator/Image_Creator/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
```

**Option B: Create separate config file (if using subdomain)**
```bash
sudo nano /etc/nginx/sites-available/image-creator
```
(Use the full server block from nginx-image-creator.conf)

```bash
sudo ln -s /etc/nginx/sites-available/image-creator /etc/nginx/sites-enabled/
```

### 12. Test and reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 13. Verify deployment
```bash
# Check service status
sudo systemctl status image-creator

# Check if port 8000 is listening
sudo ss -tlnp | grep 8000

# Check logs
sudo journalctl -u image-creator -n 50
```

### 14. Test the application
Visit: `https://tools.lemauricienltd.com/image_creator`

## Updating the Application

For future updates, run these commands:

```bash
cd /home/imagecreator/Image_Creator
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart image-creator
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u image-creator -n 100
```

### Check if port 8000 is in use
```bash
sudo ss -tlnp | grep 8000
```

### Test Gunicorn manually
```bash
cd /home/imagecreator/Image_Creator
source venv/bin/activate
gunicorn -c gunicorn_config.py wsgi:app
```

### Check Nginx error logs
```bash
sudo tail -f /var/log/nginx/tracking-server-error.log
```
