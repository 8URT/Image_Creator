#!/bin/bash
# Script to check what services are running on the droplet

echo "=== SYSTEM SERVICES ==="
echo ""
echo "Active systemd services:"
systemctl list-units --type=service --state=running | grep -v "systemd\|dbus\|NetworkManager\|ssh" | head -20

echo ""
echo "=== NGINX CONFIGURATION ==="
echo ""
echo "Nginx sites enabled:"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "No sites-enabled directory found"

echo ""
echo "=== LISTENING PORTS ==="
echo ""
echo "Ports in use:"
sudo netstat -tlnp 2>/dev/null | grep LISTEN || sudo ss -tlnp | grep LISTEN

echo ""
echo "=== GUNICORN/PYTHON PROCESSES ==="
echo ""
ps aux | grep -E "(gunicorn|python|flask)" | grep -v grep

echo ""
echo "=== APPLICATION DIRECTORIES ==="
echo ""
echo "Checking common application locations:"
ls -la /home/*/ 2>/dev/null | grep -E "^d" | awk '{print $9}' | grep -v "^\.$"
ls -la /var/www/ 2>/dev/null | head -10
ls -la /opt/ 2>/dev/null | head -10

echo ""
echo "=== NGINX CONFIG FILES ==="
echo ""
echo "Main nginx config:"
sudo cat /etc/nginx/nginx.conf 2>/dev/null | grep -E "(server_name|listen|proxy_pass)" | head -20

echo ""
echo "=== SYSTEMD SERVICE FILES ==="
echo ""
echo "Custom service files:"
ls -la /etc/systemd/system/*.service 2>/dev/null | grep -v "systemd\|dbus\|getty"
