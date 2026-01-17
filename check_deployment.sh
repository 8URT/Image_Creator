#!/bin/bash
# Script to check deployment status and configuration

echo "=== NGINX SITES ENABLED ==="
echo ""
ls -la /etc/nginx/sites-enabled/
echo ""

echo "=== NGINX CONFIGURATION FILES ==="
echo ""
for file in /etc/nginx/sites-enabled/*; do
    if [ -f "$file" ]; then
        echo "--- $file ---"
        cat "$file" | grep -E "(server_name|listen|proxy_pass|root|location)" | head -30
        echo ""
    fi
done

echo "=== LISTENING PORTS ==="
echo ""
sudo ss -tlnp | grep LISTEN | awk '{print $4, $5}' | sort -u

echo ""
echo "=== SYSTEMD SERVICE FILES (Custom) ==="
echo ""
ls -la /etc/systemd/system/*.service 2>/dev/null | grep -v "systemd\|dbus\|getty\|polkit\|ssh\|cron\|rsyslog" | awk '{print $9}'

echo ""
echo "=== GUNICORN/PYTHON PROCESSES ==="
echo ""
ps aux | grep -E "(gunicorn|python|flask)" | grep -v grep

echo ""
echo "=== APPLICATION DIRECTORIES ==="
echo ""
echo "Home directories:"
ls -la /home/ 2>/dev/null
echo ""
echo "WWW directories:"
ls -la /var/www/ 2>/dev/null
echo ""
echo "Opt directories:"
ls -la /opt/ 2>/dev/null | head -10

echo ""
echo "=== CHECKING FOR IMAGE CREATOR ==="
echo ""
find /home /var/www /opt -name "Image_Creator" -o -name "image-creator" -o -name "image_creator" 2>/dev/null
