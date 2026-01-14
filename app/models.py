from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_auth_method(self):
        """Return authentication method"""
        if self.google_id:
            return 'Google'
        elif self.password_hash:
            return 'Password'
        return 'Unknown'

class TemplateConfig(db.Model):
    """Template configuration for tools"""
    __tablename__ = 'template_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    tool_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_json = db.Column(db.Text, nullable=False)  # JSON string
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def get_config(self):
        """Get config as dictionary"""
        try:
            return json.loads(self.config_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_config(self, config_dict):
        """Set config from dictionary"""
        self.config_json = json.dumps(config_dict)
    
    def __repr__(self):
        return f'<TemplateConfig {self.tool_name}>'

class UsageLog(db.Model):
    """Usage logging for analytics"""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tool_name = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    def __repr__(self):
        return f'<UsageLog {self.user_id} - {self.tool_name} - {self.timestamp}>'
