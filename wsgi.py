"""WSGI entry point for Gunicorn"""
from app import create_app
import os

# Create the Flask application instance
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()
