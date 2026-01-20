#!/bin/bash
# Deployment commands for Image Creator
# Run these commands on the droplet as root

echo "=== Step 1: Check/Create imagecreator user ==="
if id "imagecreator" &>/dev/null; then
    echo "User imagecreator already exists"
else
    echo "Creating imagecreator user..."
    adduser --disabled-password --gecos "" imagecreator
    usermod -aG www-data imagecreator
fi

echo ""
echo "=== Step 2: Create application directory ==="
mkdir -p /opt/image-creator
chown imagecreator:www-data /opt/image-creator

echo ""
echo "=== Step 3: Switch to imagecreator user and clone repo ==="
echo "Run these commands as imagecreator user:"
echo ""
echo "su - imagecreator"
echo "cd /opt/image-creator"
echo "git clone git@github.com:8URT/Image_Creator.git ."
echo "python3 -m venv venv"
echo "source venv/bin/activate"
echo "pip install -r requirements.txt"
echo "cp env.example .env"
echo "# Edit .env file with your settings"
echo "flask db init"
echo "flask db migrate -m 'Initial migration'"
echo "flask db upgrade"
echo ""
echo "=== Step 4: Create systemd service (as root) ==="
echo "Create /etc/systemd/system/image-creator.service with:"
cat << 'EOF'
[Unit]
Description=Image Creator Gunicorn daemon
After=network.target

[Service]
User=imagecreator
Group=www-data
WorkingDirectory=/opt/image-creator
Environment="PATH=/opt/image-creator/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/image-creator/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "=== Step 5: Enable and start service (as root) ==="
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable image-creator"
echo "sudo systemctl start image-creator"

echo ""
echo "=== Step 6: Configure Nginx ==="
echo "Edit /etc/nginx/sites-available/tracking-server"
echo "Add location /image_creator block before location /"
