#!/bin/bash
# Deployment script for DigitalOcean droplet

set -e

echo "Starting deployment..."

# Activate virtual environment
source venv/bin/activate

# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade

# Restart Gunicorn
sudo systemctl restart image-creator

echo "Deployment complete!"
