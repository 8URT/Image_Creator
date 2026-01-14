# Deployment Guide for Social Image Creator

## Prerequisites

- DigitalOcean droplet (Ubuntu 20.04+)
- Domain name pointing to droplet IP (tools.lemauricien.com)
- Google OAuth credentials (optional but recommended)

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx git

# Create application user (optional but recommended)
sudo adduser --disabled-password --gecos "" imagecreator
```

### 2. Clone Repository

```bash
# Switch to application user
sudo su - imagecreator

# Clone repository
git clone git@github.com:8URT/Image_Creator.git
cd Image_Creator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env
```

Required environment variables:
- `SECRET_KEY` - Generate a strong secret key
- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret
- `BASE_URL` - https://tools.lemauricien.com
- `ADMIN_EMAIL` - Your admin email address

### 4. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Configure Gunicorn

Create systemd service file:

```bash
sudo nano /etc/systemd/system/image-creator.service
```

Add the following:

```ini
[Unit]
Description=Image Creator Gunicorn daemon
After=network.target

[Service]
User=imagecreator
Group=www-data
WorkingDirectory=/home/imagecreator/Image_Creator
Environment="PATH=/home/imagecreator/Image_Creator/venv/bin"
ExecStart=/home/imagecreator/Image_Creator/venv/bin/gunicorn -c gunicorn_config.py app:app

[Install]
WantedBy=multi-user.target
```

Start and enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl start image-creator
sudo systemctl enable image-creator
```

### 6. Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/image-creator
sudo ln -s /etc/nginx/sites-available/image-creator /etc/nginx/sites-enabled/

# Update paths in nginx.conf
sudo nano /etc/nginx/sites-available/image-creator
# Change /path/to/Social_Image_Creator to /home/imagecreator/Image_Creator

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d tools.lemauricien.com

# Auto-renewal is set up automatically
```

### 8. Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Post-Deployment

### Create Admin User

The application automatically creates a default admin user on first run. To change the password:

1. Log in with the default credentials (check .env for ADMIN_EMAIL)
2. Go to Admin panel → Users
3. Edit your user and set a new password

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://tools.lemauricien.com/auth/google/callback`
6. Copy Client ID and Secret to `.env` file
7. Restart the application: `sudo systemctl restart image-creator`

## Maintenance

### Update Application

```bash
cd /home/imagecreator/Image_Creator
source venv/bin/activate
git pull
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart image-creator
```

### View Logs

```bash
# Application logs
sudo journalctl -u image-creator -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup Database

```bash
# SQLite database backup
cp /home/imagecreator/Image_Creator/image_creator.db /backup/location/
```

## Troubleshooting

### Application not starting
- Check logs: `sudo journalctl -u image-creator -n 50`
- Verify virtual environment is activated
- Check database permissions

### 502 Bad Gateway
- Verify Gunicorn is running: `sudo systemctl status image-creator`
- Check Nginx configuration: `sudo nginx -t`
- Verify port 8000 is accessible

### Static files not loading
- Check Nginx static file path
- Verify file permissions
- Check Nginx error logs
