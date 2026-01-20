import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///image_creator.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    # Restrict Google OAuth to existing users only (set to True to allow automatic user creation)
    GOOGLE_OAUTH_ALLOW_NEW_USERS = os.environ.get('GOOGLE_OAUTH_ALLOW_NEW_USERS', 'False').lower() == 'true'
    # Restrict Google OAuth to specific email domains (comma-separated, e.g., "example.com,company.com")
    GOOGLE_ALLOWED_DOMAINS = os.environ.get('GOOGLE_ALLOWED_DOMAINS')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Fallback password protection
    FALLBACK_PASSWORD_HASH = os.environ.get('FALLBACK_PASSWORD_HASH') or '6373f7e8a5733aa1b875ec0e46235b67b018e8fe239e47bc35d6d9b792cc3b2c'
    FALLBACK_PASSWORD_ENABLED = os.environ.get('FALLBACK_PASSWORD_ENABLED', 'True').lower() == 'true'
    
    # Application settings
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///image_creator_dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///image_creator.db'
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
