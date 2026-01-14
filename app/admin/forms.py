from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from app.models import User

class UserForm(FlaskForm):
    """Form for creating/editing users"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    is_admin = BooleanField('Admin')
    is_active = BooleanField('Active', default=True)
    
    def validate_email(self, field):
        """Check if email is unique (excluding current user if editing)"""
        user_id = getattr(self, '_user_id', None)
        existing_user = User.query.filter_by(email=field.data).first()
        if existing_user and (not user_id or existing_user.id != user_id):
            raise ValidationError('Email already registered.')

class TemplateConfigForm(FlaskForm):
    """Form for template configuration"""
    tool_name = StringField('Tool Name', validators=[DataRequired()])
    config_json = TextAreaField('Configuration (JSON)', validators=[DataRequired()])
