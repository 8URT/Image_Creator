# Deployment Checklist - Image Creator

## Pre-Deployment Checklist

### ✅ Code Ready
- [x] All features implemented and tested
- [x] Code committed and pushed to repository
- [x] No sensitive data in repository (.env is gitignored)

### 🔐 Environment Variables (Set on Server)
Before deployment, ensure `.env` file on server has:

```bash
# Required
SECRET_KEY=<generate-secure-key>
FLASK_ENV=production
DATABASE_URL=sqlite:///image_creator.db

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_OAUTH_ALLOW_NEW_USERS=False
GOOGLE_ALLOWED_DOMAINS=<optional-comma-separated-domains>

# Security (Production)
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Application
BASE_URL=https://tools.lemauricienltd.com
ADMIN_EMAIL=<your-admin-email>

# Fallback (Optional)
FALLBACK_PASSWORD_ENABLED=False
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 🌐 URL Configuration
**Production URL:** `https://tools.lemauricienltd.com/image_creator`

The application will be accessible at this URL after deployment.

### 📋 Deployment Steps

1. **SSH into server:**
   ```bash
   ssh root@178.128.18.58
   ```

2. **If first deployment:**
   ```bash
   # Create user
   adduser --disabled-password --gecos "" imagecreator
   usermod -aG www-data imagecreator
   
   # Switch to user
   su - imagecreator
   
   # Clone repo
   cd /home/imagecreator
   git clone git@github.com:8URT/Image_Creator.git
   cd Image_Creator
   
   # Setup venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Setup .env (copy from env.example and edit)
   cp env.example .env
   nano .env  # Add all required values
   
   # Initialize database
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/image-creator.service
   ```
   (Use content from systemd.service.example)

4. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable image-creator
   sudo systemctl start image-creator
   sudo systemctl status image-creator
   ```

5. **Configure Nginx:**
   ```bash
   sudo nano /etc/nginx/sites-available/tracking-server
   ```
   Add location block from nginx-image-creator.conf BEFORE existing `location /` block.

6. **Test and reload Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

7. **Verify deployment:**
   ```bash
   # Check service
   sudo systemctl status image-creator
   
   # Check port
   sudo ss -tlnp | grep 8000
   
   # Check logs
   sudo journalctl -u image-creator -n 50
   ```

### 🔄 For Updates (After Initial Deployment)

```bash
cd /home/imagecreator/Image_Creator
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart image-creator
```

### 🧪 Post-Deployment Testing

- [ ] Application loads at configured URL
- [ ] Login page works
- [ ] Google OAuth login works (if configured)
- [ ] Admin panel accessible
- [ ] Image Creator tool works
- [ ] All formats work (Post, Story, Website)
- [ ] Image upload works
- [ ] Download works
- [ ] Excerpt text block works

### 🐛 Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u image-creator -n 100
```

**Check port:**
```bash
sudo ss -tlnp | grep 8000
```

**Test manually:**
```bash
cd /home/imagecreator/Image_Creator
source venv/bin/activate
gunicorn -c gunicorn_config.py wsgi:app
```

**Nginx errors:**
```bash
sudo tail -f /var/log/nginx/tracking-server-error.log
```

### 🔒 Security Reminders

- ✅ `.env` file is NOT in git
- ✅ `SECRET_KEY` is strong and unique
- ✅ `SESSION_COOKIE_SECURE=True` for HTTPS
- ✅ `GOOGLE_OAUTH_ALLOW_NEW_USERS=False` (restrict access)
- ✅ Database file permissions are secure
- ✅ Nginx is configured with security headers
